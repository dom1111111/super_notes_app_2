from datetime import datetime
import numpy as np
import whisper

#-------------

class WhisperT:
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
