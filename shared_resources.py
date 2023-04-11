from datetime import datetime
from queue import Queue
from threading import Thread, Lock
from functools import wraps
from typing import Callable, ParamSpec, TypeVar
import pyttsx3

# these are system scripts
from external_scripts import stt_engine, play_rec_audio, nodes, GUI_tk


#-------------------------------
# Program Objects

class SharedSingleItemContainer:
    def __init__(self):
        self.__mutex = Lock()
        self.__item = None
    
    def set(self, data):
        with self.__mutex:      # better to use `with` (context manager), than `acquire` and `release` for locks
            self.__item = data

    def get(self):
        with self.__mutex:
            # return item value, and reset it to None
            item = self.__item
            self.__item = None  
            return item

# Program Parent Class
class PersistentProgram:
    def __init__(self, name:str, command_function):
        self.id = datetime.now().strftime(TimeTools.TIME_STR_FRMT_1)
        self.name = name

        self.user_input = SharedSingleItemContainer()
        self.active = True

        # start command thread
        t = Thread(target=command_function, daemon=True)
        t.start() 

    #---------

    def give_input_audio(self, audio_data:bytes):
        self.user_input.set(audio_data)

    def end(self):
        self.active = False

    #---------

    def _get_input_audio(self):
        return self.user_input.get()

#-------------------------------
# Object used to wrap methods to make them thread safe

T = TypeVar('T')
P = ParamSpec('P')

class SharedResourceWrapper:
    def __init__(self):
        self.mutex = Lock()

    def __call__(self, func:Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args:P.args, **kwargs:P.kwargs) -> T:
            with self.mutex:
                result = func(*args,**kwargs)
            return result
        return wrapper


#-------------------------------
# Common Functions

class WordTools:
    KEYWORDS = {                # even single word combos MUST be tuples - don't foget the comma
        'wake_words': ('computer', ),
        'get':      ('get', 'return', 'retrieve', 'show', 'display', 'read'),
        'search':   ('search', 'find', 'seek', 'look'),
        'create':   ('create','make', 'new'),   # 'write', 'start', 'compose'
        'exit':     ('exit', 'terminate', 'stop'),
        'end':      ('end', 'finish', 'complete'),
        'shutdown': ('shutdown', 'shut down', 'bye', 'goodbye', 'good bye'),
        'app':      ('app', 'application', 'system'),
        'calculate':('calculate', 'calculator', 'math'),
        'note':     ('note', 'text', 'entry', 'page'),
        'task':     ('task', 'todo'),
        'recent':   ('recent', 'latest', 'last'),
        'current':  ('current', 'present'),
        'today':    ('today', 'todays', "today's")
    }

    @classmethod
    def get_keywords_str(cls, *keys:str, all:bool=False):
        keywords = ''
        if all:
            # brings all command keywords into a list, removes duplicates, and joins them into a single string
            return ' '.join(list(dict.fromkeys([word for word_tup in cls.KEYWORDS.values() for word in word_tup])))
        for key in keys:
            for word in cls.KEYWORDS.get(key):
                keywords += word + ' '
            #keywords += ' '
        return keywords

    @classmethod
    # check if the specified keywords are present in text
    def match_keywords(cls, keyword_keys:tuple, text:str):
        assert isinstance(keyword_keys, tuple)
        match_count = 0
        for key in keyword_keys:
            keywords = cls.KEYWORDS.get(key)
            for word in keywords:
                if word in text.lower():
                    match_count += 1
                    break
        # only return True if each keyword group gets at least one match
        if match_count >= len(keyword_keys):
            return True


class TimeTools:
    TIME_STR_FRMT_1 = '%Y%m%d%H%M%S%f'
    TIME_STR_FRMT_2 = '%I:%M %p'
    DATE_STR_FRMT_1 = '%Y %B %d, %A'
    DATE_STR_FRMT_2 = '%A, %B %d'

    def validate_if_within_timeout(current_time:datetime, last_time:datetime, timeout:int):
        if (current_time - last_time).seconds <= timeout:
            return True

    @classmethod
    def today(cls):
        return datetime.now().strftime(cls.DATE_STR_FRMT_2)

    @classmethod
    def now_time(cls):
        return datetime.now().strftime(cls.TIME_STR_FRMT_2)


#-------------------------------
# All IO methods organized into static classes

class VoiceInput:
    Vox = stt_engine.VoiceToText()
    ALPHABET = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z"

    start_listening = Vox.start_listening
    stop_listening = Vox.stop_listening
    get_audio_phrase = Vox.get_audio_phrase
    transcribe_audio = Vox.transcribe_audio

    @classmethod
    def common_transcribe_audio(cls, audio_data:bytes) -> str:
        vocab = None # VOCAB IS ALL STANDARD KEYWORDS + NUMER WORDS
        transcription = cls.Vox.transcribe_audio(audio_data, )
        # add code to convert number words to numbers intelgently
        return transcription


class VoiceOutput:
    tts_eng = pyttsx3.init()

    @classmethod
    def say(cls, mes:str):
        cls.tts_eng.say(mes)
        cls.tts_eng.runAndWait()
    
    @classmethod
    def shutup(cls):
        cls.tts_eng.stop()


class AudioOutput:
    __wrap = SharedResourceWrapper()


class Terminal():
    __wrap = SharedResourceWrapper()

    @__wrap
    def nl_print(message:str):
        print('\n' + message)


class GUI:
    #windows
    __wrap = SharedResourceWrapper()

    start_GUI = GUI_tk.run_GUI
    end_GUI = GUI_tk.terminate_GUI
    output_to_mainview = __wrap(GUI_tk.append_to_mainview)
    clear_mainview = __wrap(GUI_tk.clear_mainview)

    #new_window


class Storage:
    files = nodes.ReadWriteNodes()
    __wrap = SharedResourceWrapper()

    create_node = __wrap(files.create_node)
