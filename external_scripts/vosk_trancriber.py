from vosk import Model, KaldiRecognizer, SetLogLevel
import json

#-------------

word_list = '["computer cool guy alexander good bye", "oh zero one two three four five six seven eight nine", "[unk]"]'
# word_list must be a string of a list of words
# "[unk]" must be included. If it isn't, then one of the word will always be returned (even if you didn't say them)

#-------------

class VoskT:
    def __init__(self):
        self.tiny_model_path = "vosk_models/vosk-model-small-en-us-0.15"
        self.small_model_path = "vosk_models/vosk-model-en-us-0.22-lgraph"
        # SetLogLevel(-1)                   # disables kaldi output messages

        # load model and recognizer
        model = Model(model_path=self.tiny_model_path, lang='en-us')
        self.rec = KaldiRecognizer(model, 16000, word_list)    
        self.rec.SetWords(False)            # set this to true to have results come with time and confidence

    def transcribe(self, audio_data):
        # transcribe audio
        self.rec.AcceptWaveform(audio_data)
        json_result = self.rec.Result()

        # get text of transcription
        dict_result = json.loads(json_result)
        text = dict_result.get('text')
        # this makes sure to remove "[unk]" from text
        text = text.replace('[unk] ', '')
        text = text.replace('[unk]', '')

        return text
