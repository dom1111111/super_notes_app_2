from time import sleep
from datetime import datetime

from external_scripts import stt_engine, play_rec_audio, whisper_transcriber #, VoskT
from external_scripts import GUI_tk as GUI

#-------------------------------
# Common shared functions

time_str_format_1 = '%Y%m%d%H%M%S%f'
common_keywords = {                # even single word combos MUST be tuples - don't foget the comma
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
def match_keywords(keyword_names:tuple, text:str):
    match_count = 0
    for key in keyword_names:
        keywords = common_keywords.get(key)
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

#-------------------------------

class CoreFunctions:
    def __init__(self):
        self.loop = False
        self.sub_progs = []                             # should store active sub-program objects

    def redo(self):
        pass

    def undo(self):
        pass

    def end_loop(self):
        self.loop = False

    def spawn_sub_program(self, program_object, name:str):
        self.nl_print(f'starting sub_program: "{name}"')
        prog = program_object(name)                     # instatiate the object
        self.sub_progs.append(prog)                     # add object to sub_progs list
        self.sub_progs.sort(key=lambda x: x.priority)   # sort sub_progs list by object attribute: "priority"

    def terminate_sub_program(self, id:str):
        for prog in self.sub_progs:
            if prog.id == id:
                i = self.sub_progs.index(prog)
                self.sub_progs.pop(i)
                break

#-------------------------------

class InputOutput:
    def __init__(self):
        self.vox = stt_engine.VoiceToText(whisper_transcriber.WhisperT)

    def nl_print(self, x:str=None):
        print('\n'+x)

    #---------
    # Voice input from mic

    def start_voice_input(self):
        self.vox.start_listening()

    def get_voice_input(self):
        return self.vox.get_transcribed_phrase()
    
    #def get_current_input_text(self):
    #    pass

    def end_voice_input(self):
        self.vox.stop_listening()

    def use_full_vocabulary(self):
        pass

    def set_vocabulary(self, words:tuple):
        pass
    
    def add_to_vocabulary(self, words:tuple):
        pass

    def reset_vocabulary(self):
        pass

    #---------
    # GUI

    def start_GUI(self):
        """this must be called from the main thread, and will persist - will not return!"""
        GUI.run_GUI()

    def end_GUI(self):
        GUI.terminate_GUI()

    def output_to_log(self, message:str):
        GUI.append_to_log(message)

    def output_to_main_view(self, message:str):
        GUI.append_to_mainview(message)

    def clear_main_view(self):
        GUI.clear_mainview()

#-------------------------------

coms = AppCommands()