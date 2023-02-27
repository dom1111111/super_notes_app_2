from datetime import datetime
from time import sleep
from multiprocessing import Process, Queue, Event, cpu_count
from threading import Thread
import numpy as np
import pyaudio
import whisper

#-------------

# 3. transcribe phrase
def whisper_transcribe_phrase(untranscribed_q, transcribed_q, flag, proc_id):
    
    # load the model first, then let the other processes know that they're good to go
    whisper_model = whisper.load_model("tiny.en") # choice between ["tiny", "base", "small", "medium", "large"]
    transcribed_q.put('ready!')

    while flag.is_set():
        while True:
            # get phrase dict package
            try:
                phrase = untranscribed_q.get(timeout=0.01)
            except:
                break
            # transcribe its audio data to text
            audio_data = phrase.get('audio data')
            audio = np.frombuffer(audio_data, np.int16).flatten().astype(np.float32) / 32768.0
            audio = whisper.pad_or_trim(audio)
            result = whisper_model.transcribe(audio, language='English')

            # update phrase with new data
            timestamp = phrase.get('timestamp')
            phrase.update({
                'process id'    : proc_id,
                'trans time'    : str(datetime.now() - timestamp)[5:-3],
                'text'          : result.get('text')
            })
            # validate quality of the transcription
            trans_data = result.get('segments')
            if (trans_data) and (trans_data[0].get('no_speech_prob') < 0.1):    # the lower the comparison float, the more strict it is
                phrase.update({'trans quality' : True})
            else:
                phrase.update({'trans quality' : False})
            # repackage the processed phrase into a dictionary where the key is the timestamp
            # and the value is the existing phrase dictionary, and then sent it into the next queue
            transcribed_q.put({timestamp: phrase})


#-------------

class VoiceController:
    """
    `start_listening` to start listening for phrases and transcribing voice to text
    
    `get_phrase_text` to retrieve the transcription
    
    `stop_listening` to stop everything
    """
    def __init__(self):
        self.p = pyaudio.PyAudio()

        self.audio_threshold = 675                  # value from 0-65535 (65535 is the max possible value for int16 array (unbalanced) of audio data) 
        self.minimum_phrase_length = 0.3            # in seconds
        self.chunks_per_second = 5
        self.phrase_chunks = []                     # holds the recorded audio data chunks which are above the threshold

        self.flag = Event()                         # event object to manage activeness of looping functions in other processes
        self.proc_list = []                         # list to hold process objects - which can then be refferenced to fully terminate processes

        self.untranscribed_q = Queue()              # holds audio data for phrases, ready for transcription
        self.transcribed_q = Queue()                # holds the transcribed audio text
        self.unvalidated_phrases = {}               # holds phrases and their meta data in order, to be joined with trancriptions and validated
        self.valid_phrase_q = Queue()               # holds the validated phrases, ready to be used by other processes


    #-------------
    # Audio related methods

    def __get_audio_power(self, data):
        data_array = np.frombuffer(data, dtype="int16")
        sample_value_range = abs(int(np.max(data_array)) - int(np.min(data_array)))
        # mean_sample_value = mean(abs(audio_data_array))
        return sample_value_range

    # 2. capture phrases from audio stream
    def __detect_phrase(self, chunk):
        audio_power = self.__get_audio_power(chunk)
        minimum_chunks = round(self.minimum_phrase_length * self.chunks_per_second)

        if audio_power > self.audio_threshold:
            self.phrase_chunks.append(chunk)
        
        elif audio_power < self.audio_threshold and self.phrase_chunks:
            if len(self.phrase_chunks) >= minimum_chunks:
                self.phrase_chunks.append(chunk)
                timestamp = datetime.now()
                phrase_audio_data = b''.join(self.phrase_chunks)
                phrase = {
                    'timestamp'     : timestamp,
                    'audio power'   : self.__get_audio_power(phrase_audio_data),
                    'audio data'    : phrase_audio_data,
                    'process id'    : None,
                    'trans time'    : None,
                    'trans quality' : None,
                    'text'          : None
                }
                self.untranscribed_q.put(phrase)
                self.unvalidated_phrases.update({timestamp: phrase})

            # regardless of above condition, clear phrase_chunks
            self.phrase_chunks.clear()

    # 1. record audio stream
    def __start_stream(self):
        self.__stop_stream()                    # close the stream if one is already open

        def callback(in_data, frame_count, time_info, status):
            self.__detect_phrase(in_data)
            return (in_data, pyaudio.paContinue)

        SAMPLE_RATE = 16000
        self.stream = self.p.open(
            format = pyaudio.paInt16,           # 16 bit depth (2 bytes long)
            rate = SAMPLE_RATE,
            channels = 1,
            frames_per_buffer = round(SAMPLE_RATE/self.chunks_per_second),     # buffer size
            input = True,
            stream_callback = callback
            )

    def __stop_stream(self):
        if hasattr(self, 'stream'):
            self.stream.close()


    #-------------
    # Transcribing related methods

    def __start_multi_transcribing_processes(self):
        # check how many cores this computer has
        cc = cpu_count()
        n_proc = 3 if cc > 3 else cc

        # start the processes
        for x in range(n_proc):   
            t_proc = Process(
                target= whisper_transcribe_phrase, 
                args=   (self.untranscribed_q, self.transcribed_q, self.flag, x), 
                daemon= True
            )
            t_proc.start()
            self.proc_list.append(t_proc)
        
        proc_loading_counter = 0

        while not proc_loading_counter >= n_proc:
            self.transcribed_q.get()
            proc_loading_counter += 1

    # 4. validate phrase
    def __validate_phrase(self):
        while self.flag.is_set():
            # get any available phrases that have been transcribed and merge them with the same one in unvalidate_phrases
            try:
                trancribed_phrase = self.transcribed_q.get(timeout=0.01)
                self.unvalidated_phrases.update(trancribed_phrase)
            except:
                pass

            while True:
                # check that unvalidated_phrases isn't empty
                if not self.unvalidated_phrases:
                    break

                # collect the earliest phrase and its data into variables
                earliest_timestamp = min(self.unvalidated_phrases)
                
                phrase = self.unvalidated_phrases.get(earliest_timestamp)

                trans_time = phrase.get('trans time')
                # check if this earliest phrase has been transcribed, otherwise break and try again
                # this makes sure things are in order
                if not trans_time:
                    break

                # remove phrase from unvalidated_phrases
                self.unvalidated_phrases.pop(earliest_timestamp)

                #---

                # get phrase data into variables
                timestamp = phrase.get('timestamp')
                audio_power = phrase.get('audio power')
                audio_data = phrase.get('audio data')
                # proc_id = phrase.get('process id')
                # trans_time = phrase.get('trans time')
                trans_quality = phrase.get('trans quality')
                text = phrase.get('text')
                
                # validate the phrase's transcription quality
                if not trans_quality:
                    break

                # if above conitions are met, send on the phrase
                self.valid_phrase_q.put(
                    {
                        'timestamp' : timestamp,
                        'audio power':audio_power,
                        'audio data': audio_data,
                        'text'      : text
                    }
                )

                # then break the loop and start over                
                break
                

    def __start_phrase_validator(self):
        pv = Thread(target=self.__validate_phrase, daemon=True)
        pv.start()


    #-------------
    # Main accessible methods

    def start_listening(self):
        self.flag.set()
        self.__start_multi_transcribing_processes()
        self.__start_phrase_validator()
        self.__start_stream()

    def get_valid_phrase(self) -> dict:
        try:
            phrase = self.valid_phrase_q.get(timeout=0.01)
            return phrase
        except:
            pass

    def stop_listening(self):
        self.__stop_stream()
        sleep(0.5)
        self.flag.clear()
        sleep(0.5)
        for proc in self.proc_list:
            proc.terminate()            # first terminate process
        sleep(0.5)
        for proc in self.proc_list:
            proc.close()                # then completely release any resources the process was keeping
