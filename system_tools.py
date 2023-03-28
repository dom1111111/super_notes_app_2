
from time import sleep
from datetime import datetime
from threading import Lock

from external_scripts import stt_engine, play_rec_audio, nodes, GUI_tk

#-------------------------------

class SharedResourceWrapper:
    def __init__(self):
        self.mutex = Lock()

    def __call__(self, func):
        def wrapper(*args,**kwargs):
            with self.mutex:
                func(*args,**kwargs)
        return wrapper    

#-------------------------------

class GeneralTools:
    TIME_STR_FRMT_1 = '%Y%m%d%H%M%S%f'
    KEYWORDS = {                # even single word combos MUST be tuples - don't foget the comma
        'app_command_word': ('computer', ),
        'get':      ('get', 'return', 'retrieve', 'show', 'display', 'read'),
        'search':   ('search', 'find', 'seek', 'look'),
        'create':   ('create','make', 'new'),   # 'write', 'start', 'compose'
        'exit':     ('exit', 'shutdown', 'shut down', 'terminate', 'stop', 'bye', 'goodbye', 'good bye'),
        'end':      ('end', 'finish', 'complete'),
        'app':      ('app', 'application', 'program', 'computer'),
        'note':     ('note', 'text', 'entry', 'page'),
        'task':     ('task', 'todo', 'to-do'),
        'recent':   ('recent', 'latest', 'last'),
        'current':  ('current', 'present'),
        'today':    ('today', 'todays', "today's")
    }

    # check if the specified keywords are present in text
    @classmethod
    def match_keywords(cls, keyword_names:tuple, text:str):
        match_count = 0
        for key in keyword_names:
            keywords = cls.KEYWORDS.get(key)
            for word in keywords:
                if word in text.lower():
                    match_count += 1
                    break
        # only return True if each keyword group gets at least one match
        if match_count >= len(keyword_names):
            return True

    def validate_if_within_timeout(current_time:datetime, last_time:datetime, timeout):
        if (current_time - last_time).seconds <= timeout:
            return True


class VoiceInput:
    Vox = stt_engine.VoiceToText()

    @classmethod
    def start_listening(cls):
        cls.Vox.start_listening()
    
    @classmethod
    def stop_listening(cls):
        cls.Vox.stop_listening()

    @classmethod
    def get_phrase(cls):
        cls.Vox.get_audio_phrase()

    @classmethod
    def transcribe_audio(cls):
        cls.Vox.transcribe_audio()


class TerminalOutput():
    wrap = SharedResourceWrapper()

    @wrap
    def nl_print(message:str=None):
        print('\n' + message)


class AudioOutput:
    wrap = SharedResourceWrapper()


class GUI:
    wrap = SharedResourceWrapper()

    def start_GUI():
        GUI_tk.run_GUI()
    
    def end_GUI():
        GUI_tk.terminate_GUI()
    
    @wrap
    def output_to_mainview():
        GUI_tk.append_to_mainview()
    
    @wrap
    def clear_mainview(): 
        GUI_tk.clear_mainview()


class Storage:
    files = nodes.ReadWriteNodes()
    wrap = SharedResourceWrapper()

    @classmethod
    @wrap
    def create_node(cls):
        cls.files.create_node()
