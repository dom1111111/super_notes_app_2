from datetime import datetime
from time import sleep
from os import path
from queue import Queue
from threading import Thread, Lock
from functools import wraps

# these are system scripts
from external_scripts import nodes

#-------------------------------

# Program Parent Class
class PersistentProgram:
    def __init__(self, name:str, program_function):
        """
        This is the parent class for programs. All programs should inherit this class.

        Arguments:
        * `name` is for the name pf the program; should be a string
        * `program_function` is the main program function, which will be run in a loop and in a new thread. 
        If the function is not meant to be looped, then `self.active` should be set to `False` at the end of the function
        """
        self.name = name
        self.user_input = Queue()
        self.active = True
        # start command thread:
        def program_function_loop():
            while self.active:
                program_function()
        Thread(target=program_function_loop, daemon=True).start()

    #---------

    def give_input(self, i):
        """
        `i` should be a string or audio data bytes
        """
        self.user_input.put(i)

    def end(self):
        self.active = False

#-------------------------------
# Common Functions

class WordTools:
    KEYWORDS = {                # even single word combos MUST be tuples - don't foget the comma
        'wake_words': ('computer', ),
        'get':      ('get', 'return', 'retrieve', 'show', 'display', 'read'),
        'what':     ('what', "what's", 'what is'),
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
        'current':  ('current', 'present', 'now'),
        'time':     ('time', ),
        'date':     ('date', ),
        'today':    ('today', 'todays', "today's"),
        'sound':    ('sound', 'audio', 'noise')
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
    def get_current_time(cls):
        return datetime.now().strftime(cls.TIME_STR_FRMT_2)

    @classmethod
    def get_current_date(cls):
        return datetime.now().strftime(cls.DATE_STR_FRMT_2)


#-------------------------------
# All IO methods organized into static classes

class Storage:
    files = nodes.ReadWriteNodes()
    create_node = files.create_node
