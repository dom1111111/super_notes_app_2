from threading import Thread, Lock
from queue import Queue
from datetime import datetime

import system_tools as ST
import programs_commands as PC

#-------------------------------
"""
class MainProgram:
    def __init__(self):
        # stores all commands which can be done by input as the base level
        self.input_command_reference = [
            #{
            #    'name':         'New Note',
            #    'condition':    ('create', 'note'),
            #    'command':      (self.spawn_program, PC.CreateNoteQuick)
            #},
            {
                'name':         'Calculator',
                'condition':    ('calculate'),
                'command':      ST.func_wrap(self.spawn_program, PC.Calculator)
            },
            # undo
            # redo
        ]

        self.command_keyword_list_str = ST.get_keywords(all=True)

    def main(self):
        # check each command's condition
        for command_dict in self.input_command_reference:
            # check the comand's condition
            keyword_tup = command_dict.get('condition')
            passed = ST.match_keywords(keyword_tup, input_text)
            # if the condition passes, then call its function and break the loop
            if passed:
                self.last_wake_time = None              # reset wake time
                name = command_dict.get('name')
                ST.Terminal.nl_print(f'doing command: {name}')
                command = command_dict.get('command')
                command()                               # do command!
            break         

"""


class Main:
    def __init__(self):
        self.loop = False
        self.current_prog_focus = None
        self.last_sys_focus_time = None
        self.sys_focus_timeout = 5       # in seconds

        self.system_keywords = ST.get_keywords('wake_words', 'shutdown', 'app')

    #---------

    def main_loop(self):
        while self.loop:
            # [1] check for input - restart loop if none
            input_audio = ST.VoiceInput.get_audio_phrase()                                          # this is blocking
            if not input_audio:
                continue
            input_time = datetime.now()
            input_text = ST.VoiceInput.transcribe_audio(input_audio, self.system_keywords)
            if not input_text:
                continue
            ST.Terminal.nl_print(' > voice: ' + input_text)

            # [2] check if input meets system focus condition (either has wake_words or within timeout)
            if ST.match_keywords(('wake_words', ), input_text):
                sys_focus = True
            elif self.last_wake_time and ST.validate_if_within_timeout(input_time, self.last_wake_time, self.sys_focus_timeout):
                sys_focus = True
            else:
                sys_focus = False

            # [3] if sys_focus, check input for basic system commands
            if sys_focus:
                #TODO: SET GUI BOTTOM BAR TO TURN GREEN or something + make audio cue
                ST.Terminal.nl_print('WAKING!')
                self.last_wake_time = datetime.now()
                # check each command's condition
                ## SHUTDOWN
                if ST.match_keywords(('shutdown', ), input_text):
                    self.shutdown()

            # [4] if not sys_focus, send input to currently in focus program
            elif self.current_prog_focus:
                prog_id = self.current_prog_focus
                prog = self.progs.get(prog_id)
                prog.give_input_audio(input_audio)
            
            # append command stuff to the log?



#-------------------------------

if __name__ == "__main__":
    m = System()
    m.run()
    print('goodbye!')