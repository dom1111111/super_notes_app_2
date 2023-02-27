from time import sleep
from datetime import datetime

import GUI_tk as GUI
import stt_engine
import play_rec_audio

#-------------------------------

class AppCommands:
    def __init__(self):
        self.loop = False
        self.sub_progs = []                     # should store active program objects
        self.vox = stt_engine.VoiceController()
        
        self.time_str_format_1 = '%Y%m%d%H%M%S%f'
        self.common_keywords = {                # even single word combos MUST be tuples - don't foget the comma
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

    #---------
    # General Functions

    # check if the specified keywords are present in text
    def match_keywords(self, keyword_names:tuple, text:str):
        match_count = 0
        for key in keyword_names:
            keywords = self.common_keywords.get(key)
            for word in keywords:
                if word in text.lower():
                    match_count += 1
                    break
        # only return True if each keyword group gets at least one match
        if match_count >= len(keyword_names):
            return True

    def validate_if_within_timeout(self, current_time:datetime, last_time:datetime, timeout):
        if (current_time - last_time).seconds <= timeout:
            return True

    #---------
    # System Functions

    def run_GUI(self):
        GUI.run_GUI()   # THIS MUST BE CALLED ONCE, AND WILL PERSIST

    def start_core_procs(self):
        self.nl_print('loading voice input...')
        self.vox.start_listening()
        self.nl_print('voice input now active!')

    def end_core_procs(self):
        self.nl_print('shutting down...')
        self.nl_print('ending voice input...')
        self.vox.stop_listening()
        sleep(1)
        self.nl_print('voice input now off')
        GUI.terminate_GUI()

    def end_loop(self):
        self.loop = False
    
    def redo(self):
        pass

    def undo(self):
        pass

    def spawn_sub_program(self, program_object, name:str):
        self.nl_print(f'starting sub_program: "{name}"')
        prog = program_object(name)
        self.sub_progs.append(prog)

    def terminate_sub_program(self, name_id:str):
        for prog in self.sub_progs:
            if prog.name_id == name_id:
                i = self.sub_progs.index(prog)
                self.sub_progs.pop(i)
                break

    #---------
    #IO Funcs

    def get_voice_input(self):
        return self.vox.get_valid_phrase()

    def nl_print(self, x:str=None):
        print('\n'+x)

    def output_to_log(self, message:str):
        GUI.append_to_log(message)

    def output_to_main_view(self, message:str):
        GUI.append_to_mainview(message)

    def clear_main_view(self):
        GUI.clear_mainview()

#-------------------------------

coms = AppCommands()