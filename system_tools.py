from datetime import datetime
from queue import Queue
from threading import Thread, Lock
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from external_scripts import stt_engine, play_rec_audio, nodes, GUI_tk

#-------------------------------
# Tools for Programs

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

# Sub-Program Parent Class
class PersistentCommand:
    def __init__(self, name:str, command_function):
        self.time_id = datetime.now().strftime(TimeTools.TIME_STR_FRMT_1)
        self.name = name

        self.vocabulary = None
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

    def get_input_audio(self):
        return self.user_input.get()

#-------------------------------
# wraps functions so that arguments can be given easier without yet calling the function

def func_wrap(func, *args):
    def wrapper():
        func(*args)
    return wrapper

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
# All main methods organized into static classes

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
    def get_keywords(cls, *keys:str, all:bool=False):
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

    def validate_if_within_timeout(current_time:datetime, last_time:datetime, timeout):
        if (current_time - last_time).seconds <= timeout:
            return True


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


#-------------------------------

class System:
    active = False
    """
    # active sub-program objects
    progs = {}
    
    @classmethod
    def spawn_program(cls, program_object):
        Terminal.nl_print(f'starting sub_program: "{program_object.__name__}"')
        prog = program_object()                             # instatiate the object
        prog_id = prog.id
        cls.progs.update({prog_id: prog})                  # add object to sub_progs list
        cls.current_prog_focus = prog_id                   # update current program focus

    @classmethod
    def terminate_program(cls, id:str):
        prog = cls.progs.get(id)
        prog.end()
        cls.progs.pop(id)
        # reset current program focus if this program was the one in focus
        if cls.current_prog_focus == id:
            cls.current_prog_focus = None
    """
    def run(self):
        Terminal.nl_print('loading system...')
        self.active = True
        # start voice transcriber
        VoiceInput.start_listening()
        """
        # start main loop in new thread
        # main_t = Thread(target=self.main_loop, daemon=True)
        # main_t.start()
        """
        Terminal.nl_print('started!')
        # start GUI
        GUI_tk.run_GUI()         # must be called from main thread, will persist

    def shutdown(self):
        Terminal.nl_print('shutting down...')
        self.active = False
        VoiceInput.stop_listening()
        """
        #for prog in self.progs:
        #    self.terminate_program(prog.id)
        """
        GUI.end_GUI()