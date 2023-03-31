from datetime import datetime
from queue import Queue
from threading import Thread, Lock
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from external_scripts import stt_engine, play_rec_audio, nodes, GUI_tk

#-------------------------------
# General Tools

TIME_STR_FRMT_1 = '%Y%m%d%H%M%S%f'
KEYWORDS = {                # even single word combos MUST be tuples - don't foget the comma
    'app_command_word': ('computer', ),
    'get':      ('get', 'return', 'retrieve', 'show', 'display', 'read'),
    'search':   ('search', 'find', 'seek', 'look'),
    'create':   ('create','make', 'new'),   # 'write', 'start', 'compose'
    'exit':     ('exit', 'terminate', 'stop'),
    'end':      ('end', 'finish', 'complete'),
    'shutdown': ('shutdown', 'shut down', 'bye', 'goodbye', 'good bye'),
    'app':      ('app', 'application', 'system'),
    'note':     ('note', 'text', 'entry', 'page'),
    'task':     ('task', 'todo'),
    'recent':   ('recent', 'latest', 'last'),
    'current':  ('current', 'present'),
    'today':    ('today', 'todays', "today's")
}

# check if the specified keywords are present in text
def match_keywords(keyword_keys:tuple, text:str):
    assert isinstance(keyword_keys, tuple)
    match_count = 0
    for key in keyword_keys:
        keywords = KEYWORDS.get(key)
        for word in keywords:
            if word in text.lower():
                match_count += 1
                break
    # only return True if each keyword group gets at least one match
    if match_count >= len(keyword_keys):
        return True

def validate_if_within_timeout(current_time:datetime, last_time:datetime, timeout):
    if (current_time - last_time).seconds <= timeout:
        return True

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
        self.time_id = datetime.now().strftime(TIME_STR_FRMT_1)
        self.name = name
        self.vocabulary = None
        self.GUI_code = None
        self.__user_input = SharedSingleItemContainer()
        self.__active = True
        #self.__suspended = True

        self.command_function = command_function
        # start command thread
        t = Thread(target=self.__run_command, daemon=True)
        t.start() 
    
    def __run_command(self):
        self.command_function()
        # request to shut down this command
        #self.__active = False

    #---------

    def give_input(self, input_data):
        # check to make sure right type of data? - maybe implement a input_data object class?
        self.__user_input.set(input_data)

    #def suspend_toggle(self):
    #    self.__suspended = not self.__suspended

    def end(self):
        self.__active = False

    #---------

    def get_input(self):
        self.__user_input.get()

    def __make_request(self, func, args):
        request = {
            'id':   self.time_id,
            'func': func,
            'args': args
        }
        request
        self.request_q.put(request)

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
# all methods

class VoiceInput:
    Vox = stt_engine.VoiceToText()

    start_listening = Vox.start_listening
    stop_listening = Vox.stop_listening
    get_audio_phrase = Vox.get_audio_phrase
    transcribe_audio = Vox.transcribe_audio


class TerminalOutput():
    __wrap = SharedResourceWrapper()

    @__wrap
    def nl_print(message:str):
        print('\n' + message)


class AudioOutput:
    __wrap = SharedResourceWrapper()


class GUI:
    __wrap = SharedResourceWrapper()

    start_GUI = GUI_tk.run_GUI
    end_GUI = GUI_tk.terminate_GUI
    output_to_mainview = __wrap(GUI_tk.append_to_mainview)
    clear_mainview = __wrap(GUI_tk.clear_mainview)


class Storage:
    files = nodes.ReadWriteNodes()
    __wrap = SharedResourceWrapper()

    create_node = __wrap(files.create_node)
