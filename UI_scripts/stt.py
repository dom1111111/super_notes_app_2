"""
tools for voice transcription!

instatiate `VoiceToText` class and use its methods
"""

from os import path
import json
import numpy as np
from queue import Queue
from vosk import Model, KaldiRecognizer, SetLogLevel
import whisper
from .play_rec_audio import RecAudio

#-------------

class _PhraseDetector:
    """
    - `start_stream` to start recording audio and detecting phrases
    - `get_audio` to get a "phrase" of audio
    - `stop_stream` to stop recording
    """
    def __init__(self):
        self.rec = RecAudio()
        self.audio_threshold = 675                  # value from 0-65535 (65535 is the max possible value for int16 array (unbalanced) of audio data) 
        self.minimum_phrase_length = 0.3            # in seconds
        self.chunks_per_second = 5
        self.phrase_chunks = []                     # holds the recorded audio data chunks which are above the threshold
        self.audio_q = Queue()                      # holds audio data for phrases, ready for transcription

    def __get_audio_power(self, data):
        data_array = np.frombuffer(data, dtype="int16")
        sample_value_range = abs(int(np.max(data_array)) - int(np.min(data_array)))
        # mean_sample_value = mean(abs(audio_data_array))
        return sample_value_range

    # 2. capture phrases from audio stream
    def __detect_phrase(self, chunk:bytes):
        audio_power = self.__get_audio_power(chunk)
        minimum_chunks = round(self.minimum_phrase_length * self.chunks_per_second)

        if audio_power > self.audio_threshold:
            self.phrase_chunks.append(chunk)
        
        elif audio_power < self.audio_threshold and self.phrase_chunks:
            if len(self.phrase_chunks) >= minimum_chunks:
                self.phrase_chunks.append(chunk)
                phrase_audio_data = b''.join(self.phrase_chunks)
                # put audio into queue
                self.audio_q.put(phrase_audio_data)

            # regardless of above condition, clear phrase_chunks
            self.phrase_chunks.clear()

    # 1. record audio stream
    def start_stream(self):
        def callback_detect_phrase(in_data:bytes):
            self.__detect_phrase(in_data)
        
        self.rec.set_callback(callback_detect_phrase)       # set recording callback to `callback_detect_phrase` function
        
        SAMPLE_RATE = 16000
        self.rec.set_pars(                                  # set the recording audio parameters
            chunk_size = round(SAMPLE_RATE/self.chunks_per_second),
            n_channels = 1,
            rate = SAMPLE_RATE
        )
        
        self.rec.record()                                   # start recording!

    def stop_stream(self):
        self.rec.stop()

    def get_audio(self, no_wait:bool=False) -> bytes:
        try:
            return self.audio_q.get(block=not no_wait)
        except:
            return

#-------------

class _WhisperT:
    def __init__(self):
        self.model = whisper.load_model("tiny.en") # choice between ["tiny", "base", "small", "medium", "large"]

    def transcribe(self, audio_data):
        audio = np.frombuffer(audio_data, np.int16).flatten().astype(np.float32) / 32768.0
        audio = whisper.pad_or_trim(audio)
        result = self.model.transcribe(audio, language='English')
        text = result.get('text')

        # validate quality of the transcription
        trans_data = result.get('segments')
        if (trans_data) and (trans_data[0].get('no_speech_prob') < 0.1):    # the lower the comparison float, the more strict it is
            return text        
        else:
            return None

class _VoskT:
    def __init__(self):
        self.tiny_model_path = path.join(path.dirname(__file__), "vosk_models/vosk-model-small-en-us-0.15")
        self.small_model_path = path.join(path.dirname(__file__), "vosk_models/vosk-model-en-us-0.22-lgraph")
        SetLogLevel(-1)                     # disables kaldi output messages

        # load model and recognizer
        model = Model(model_path=self.tiny_model_path, lang='en-us')
        self.rec = KaldiRecognizer(model, 16000)    
        self.rec.SetWords(False)            # set this to true to have results come with time and confidence

    def transcribe(self, audio_data, words_to_recognize:str) -> str:
        """
        `words_to_recognize` must be a single string, with the words separated by whitespace
        """
        words = f'["{words_to_recognize}", "[unk]"]'
        # transcribe audio
        self.rec.SetGrammar(words)
        self.rec.AcceptWaveform(audio_data)
        json_result = self.rec.Result()

        # get text of transcription
        dict_result = json.loads(json_result)
        text = dict_result.get('text')
        # this makes sure to remove "[unk]" from text
        text = text.replace('[unk] ', '')
        text = text.replace('[unk]', '')

        return text

#-------------
# main functions

class VoiceToText:
    def __init__(self):
        self.listener = _PhraseDetector()
        self.limited_tran = _VoskT()
        self.full_tran = _WhisperT()

    def start_listening(self):
        self.listener.start_stream()

    def get_audio_phrase(self, no_wait:bool=False) -> bytes:
        audio = self.listener.get_audio(no_wait)
        return audio

    def transcribe_audio(self, audio_data:bytes, vocabulary:str='') -> str:
        """
        `vocabulary` must be a single string, with the words separated by whitespace
        """
        if vocabulary:
            return self.limited_tran.transcribe(audio_data, vocabulary)
        return self.full_tran.transcribe(audio_data)

    def stop_listening(self):
        self.listener.stop_stream()