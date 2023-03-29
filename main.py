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
        self.wake_words = "computer"
        self.last_wake_time = None
        self.wake_timeout = 5       # in seconds
        # stores all commands which can be done by input as the base level
        self.input_command_reference = [
            {
                'name':         'New Note',
                'condition':    ('create', 'note'),
                'command':      (self.spawn_program, PC.CreateNoteQuick)
            },
            {
                'name':         'Calculator',
                'condition':    (),
                'command':      (self.spawn_program, PC.Calculator)
            },
            {
                'name':         'Shutdown',
                'condition':    ('exit', 'app'),
                'command':      (self.shutdown, None)
            }
            # undo
            # redo
        ]
        self.command_keyword_list = #[for words in ]

    #---------

    def spawn_program(self, program_object, name:str):
        ST.TerminalOutput.nl_print(f'starting sub_program: "{name}"')
        prog = program_object(name)                     # instatiate the object
        prog_id = prog.id
        self.progs.update({prog_id: prog})                   # add object to sub_progs list

    def terminate_program(self, id:str):
        prog = self.progs.get(id)
        prog.end()
        self.progs.pop(id)

    # check conditions, spawn commands
    def check_spawn_commands(self, text):
        # [2] try getting action from input
        for command in self.input_command_reference:
            name = command.get('name')
            conditions = command.get('conditions')
            command = command.get('command')
            
            # check each of the comand's conditions - if any fail, then break the loop
            for condition in conditions:
                condition_func = condition[0]
                condition_arg = condition[1]
                passed = condition_func(condition_arg, text)
                if not passed:
                    break
            
            # if all of the conditions pass, then do the action
            if passed:
                func = command[0]
                args = command[1]

                ST.TerminalOutput.nl_print(f'starting command: {name}')
                last_wake_time = None      # reset wake time

                if args:
                    # check if there is more than one argument, by seeing if args is an iterable
                    if hasattr(args, '__iter__'):
                        func(*args)
                    else:
                        func(args)
                else:
                    func()
                
                return True

    #---------

    def main_loop(self):
        while self.loop:
            # [1] check for input - restart loop if none
            input_audio = ST.VoiceInput.get_phrase()
            if not input_audio:
                continue
            input_time = datetime.now()

            # [2] check if input is waking (either has wakeword or within wake timeout)
            if ST.VoiceInput.transcribe_audio(input_audio, self.wake_words):    # if has wakeword
                waking = True
            elif self.last_wake_time and ST.validate_if_within_timeout(input_time, self.last_wake_time, self.wake_timeout): # if within timeout
                waking = True
            else:
                waking = False

            # [3] if waking, check input for commands
            if waking:
                self.last_wake_time = datetime.now()
                input_keyword_text = ST.VoiceInput.transcribe_audio(input_audio, self.command_keyword_list) # transcribe audio featuring all possible commands keyboards
                if input_keyword_text:
                    command = self.check_spawn_commands(input_keyword_text)
                    if command:
                        # do command

            # [4] if not waking, send input to currently in focus program
            else:
                pass

            
            # append command stuff to the log

    def run(self):
        ST.TerminalOutput.nl_print('loading...')
        self.loop = True
        # start voice transcriber
        ST.VoiceInput.start_listening()
        # start main loop in new thread
        main_t = Thread(target=self.main_loop, daemon=True)
        main_t.start()
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
    #m = MainProgram()
    #m.run()
    print('goodbye!')