from threading import Thread, Lock
from queue import Queue
from datetime import datetime

import system_tools as ST
import programs_commands as PC

#-------------------------------

class MainProgram:
    def __init__(self):
        self.loop = False
        # active sub-program objects
        self.progs = {}
        self.current_prog_focus = None
        # for voice input validation
        self.last_wake_time = None
        self.wake_timeout = 5       # in seconds
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
            {
                'name':         'Shutdown',
                'condition':    ('shutdown',),
                'command':      ST.func_wrap(self.shutdown)
            }
            # undo
            # redo
        ]
        # brings all command keywords into a list, removes duplicates, and joins them into a single string
        self.command_keyword_list_str = ' '.join(list(dict.fromkeys([word for word_tup in ST.KEYWORDS.values() for word in word_tup])))

    #---------

    def spawn_program(self, program_object):
        ST.TerminalOutput.nl_print(f'starting sub_program: "{program_object.__name__}"')
        prog = program_object()                             # instatiate the object
        prog_id = prog.id
        self.progs.update({prog_id: prog})                  # add object to sub_progs list
        self.current_prog_focus = prog_id                   # update current program focus

    def terminate_program(self, id:str):
        prog = self.progs.get(id)
        prog.end()
        self.progs.pop(id)
        # reset current program focus if this program was the one in focus
        if self.current_prog_focus == id:
            self.current_prog_focus = None

    #---------

    def main_loop(self):
        while self.loop:
            # [1] check for input - restart loop if none
            input_audio = ST.VoiceInput.get_audio_phrase()                                          # this is blocking
            if not input_audio:
                continue
            input_time = datetime.now()
            input_text = ST.VoiceInput.transcribe_audio(input_audio, self.command_keyword_list_str) # transcribe audio featuring all possible commands keyboards
            if not input_text:
                continue
            ST.TerminalOutput.nl_print(' > voice: ' + input_text)

            # [2] check if input is waking (either has wakeword or within wake timeout)
            if ST.match_keywords(('app_command_word', ), input_text):                               # if has wakeword
                waking = True
            elif self.last_wake_time and ST.validate_if_within_timeout(input_time, self.last_wake_time, self.wake_timeout): # if within timeout
                waking = True
            else:
                waking = False

            # [3] if waking, check input for commands
            if waking:
                #TODO: SET GUI BOTTOM BAR TO TURN GREEN or something + make audio cue
                ST.TerminalOutput.nl_print('WAKING!')
                self.last_wake_time = datetime.now()
                # check each command's condition
                for command_dict in self.input_command_reference:
                    # check the comand's condition
                    keyword_tup = command_dict.get('condition')
                    passed = ST.match_keywords(keyword_tup, input_text)
                    # if the condition passes, then call its function and break the loop
                    if passed:
                        self.last_wake_time = None              # reset wake time
                        name = command_dict.get('name')
                        ST.TerminalOutput.nl_print(f'doing command: {name}')
                        command = command_dict.get('command')
                        command()                               # do command!
                    break 

            # [4] if not waking, send input to currently in focus program
            else:
                prog_id = self.current_prog_focus
                prog = self.progs.get(prog_id)
                prog.give_input_audio(input_audio)
            
            # append command stuff to the log?

    def run(self):
        ST.TerminalOutput.nl_print('loading...')
        self.loop = True
        # start voice transcriber
        ST.VoiceInput.start_listening()
        # start main loop in new thread
        main_t = Thread(target=self.main_loop, daemon=True)
        main_t.start()
        ST.TerminalOutput.nl_print('started!')
        # start GUI
        ST.GUI_tk.run_GUI()         # must be called from main thread, will persist

    def shutdown(self):
        ST.TerminalOutput.nl_print('shutting down...')
        self.loop = False
        ST.VoiceInput.stop_listening()
        for prog in self.progs:
            self.terminate_program(prog.id)
        ST.GUI.end_GUI()

#-------------------------------

if __name__ == "__main__":
    m = MainProgram()
    m.run()
    print('goodbye!')