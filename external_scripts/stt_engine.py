from datetime import datetime
from time import sleep
from multiprocessing import Process, Queue, cpu_count
import numpy as np
import pyaudio

#-------------

# 3. transcribing audio
def transcriber_handler(untranscribed_q, transcribed_q, transcriber):
    """
    `transcriber` must be an object which has a method called 'transcribe', which accepts the audio data and returns text.
    `None` must be returned if the trasncriber could not accurate transcribe the audio
    """
    # instatiate transcriber object
    t = transcriber()
    transcribed_q.put('transcriber loaded!')
    
    while True:
        # wait for phrase
        phrase = untranscribed_q.get()
        # if phrase is "END", then break
        if phrase == "END":
            break

        # get phrase data
        audio_data = phrase.get('audio data')
        timestamp = phrase.get('timestamp')

        # transcribe the audio
        text = t.transcribe(audio_data)

        if text:
            # update phrase with transcribed text
            phrase.update({
                'trans time':   str(datetime.now() - timestamp)[5:-3],
                'text':         text
            })
            # send transcribed phrase it into the next queue
            transcribed_q.put(phrase)


class VoiceToText:
    """
    - `start_listening` to start listening for phrases and transcribing voice to text
    - `get_transcribed_phrase` to retrieve the transcription
    - `stop_listening` to stop everything
    """
    def __init__(self, transcriber_obj):
        self.p = pyaudio.PyAudio()
        self.transcriber = transcriber_obj

        self.audio_threshold = 675                  # value from 0-65535 (65535 is the max possible value for int16 array (unbalanced) of audio data) 
        self.minimum_phrase_length = 0.3            # in seconds
        self.chunks_per_second = 5
        self.phrase_chunks = []                     # holds the recorded audio data chunks which are above the threshold

        self.untranscribed_q = Queue()              # holds audio data for phrases, ready for transcription
        self.transcribed_q = Queue()                # holds the transcribed audio text

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
                    'trans time'    : None,
                    'text'          : None
                }
                self.untranscribed_q.put(phrase)

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
    # Main accessible methods

    def start_listening(self):
        # start the transcriber process
        t_proc = Process(
            target= transcriber_handler, 
            args=   (self.untranscribed_q, self.transcribed_q, self.transcriber), 
            daemon= True
        )
        t_proc.start()
        self.transcribed_q.get()    # wait until transcriber is loaded
        # start the stream
        self.__start_stream()

    def get_transcribed_phrase(self) -> dict:
        try:
            return self.transcribed_q.get(timeout=0.01)
        except:
            return

    def stop_listening(self):
        self.__stop_stream()
        self.untranscribed_q.put("END")
        sleep(0.01)