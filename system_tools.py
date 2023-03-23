"""
this stores all of the standard functions and objects needed by the system

these functions interface with other scripts
"""

from time import sleep
from datetime import datetime

from external_scripts import stt_engine, play_rec_audio, nodes, GUI_tk, whisper_transcriber #, VoskT

#-------------------------------

Vox = stt_engine.VoiceToText()

Lib = nodes.ReadWriteNodes()

#-------------------------------
# General Tools

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

#---------
# Terminal Output

def nl_print(message:str=None):
    print('\n' + message)

#-------------------------------

# this is used soley to keep track of functions
function_refference = {
    # general tools
    'match keywords':           match_keywords,
    'is within timeout':        validate_if_within_timeout,

    # voice user input
    'start listening':          Vox.start_listening,
    'pause listening':          None,
    'stop listening':           Vox.stop_listening,
    'get phrase':               Vox.get_transcribed_phrase,
    'use full vocabulary':      None,
    'set vocabulary':           None,
    'add to vocabulary':        None,
    'reset vocabulary':         None,

    # terminal output
    'print':                    nl_print,

    # GUI + user output
    'start GUI':                GUI_tk.run_GUI,
    'end GUI':                  GUI_tk.terminate_GUI,
    'output to main view':      GUI_tk.append_to_mainview,
    'clear main view':          GUI_tk.clear_mainview,

    # storage IO
    'create node':              Lib.create_node,
}
