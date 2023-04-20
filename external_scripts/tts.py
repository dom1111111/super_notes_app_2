from os import path
import pyttsx3
from .play_rec_audio import PlayAudio

#---------

class ComputerVoice:
    def __init__(self):
        self._engine = pyttsx3.init()
        self._player = PlayAudio()
        self._file = path.join(path.dirname(__file__), 'tts.wav')
        self._current_message = ''

        # NOTE: would like to figure this out
        #_file = BytesIO()
        #with wave.open(_file, 'wb') as f:
        #    f.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))

    def say(self, message:str, wpm:int=200):
        assert isinstance(message, str) and isinstance(wpm, int)
        self._player.stop()                                 # first stops audio (and closes stream) - this is neccessary even if no audio is playing, otherwise new messages can't be created!
        self._engine.setProperty('rate', wpm)               # sets speaking rate in wpm (default is 200)
        if message != self._current_message:                # if the message is the same as the last, skip this step
            self._engine.save_to_file(message, self._file)  # create tts audio file from message
            self._engine.runAndWait()
        self._current_message = message
        self._player.play(self._file)                       # play tts audio file

    def shutup(self):
        self._player.stop()
