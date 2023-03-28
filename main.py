from threading import Thread, Lock
from queue import Queue
from datetime import datetime

import system_tools as ST
import programs_commands as PC

#-------------------------------

class Main:
    loop = False
    # active sub-program objects
    progs = {}
    current_prog_focus = None
    # for voice input validation
    last_wake_time = None
    wake_timeout = 5       # in seconds
    # stores all commands which can be done by input as the base level
    input_command_reference = [
        {
            'name':         'New Note',
            'condition':    ('create', 'note'),
            'command':      PC.CreateNoteQuick
        },
        {
            'name':         'Calculator',
            'condition':    (),
            'command':      PC.Calculator
        },
        {
            'name':         'Shutdown',
            'condition':    ('exit', 'app'),
            'command':      shutdown
        }
        # undo
        # redo
    ]

    #---------

    @classmethod
    def main_loop(cls):
        while cls.loop:
            # [1] check for input - restart loop if none
            input_package = ST.VoiceInput.get_transcribed_phrase()
            if not input_package:
                continue
            input_text = input_package.get('text')
            
            ST.TerminalOutput.nl_print(f'input: "{input_text}"')

            # [2] run main program and pass it input
            main = self.main_program(input_package)
            # check if it uses input
            if main:
                continue

            # [3] if main program didn't use input, pass it to the program/command currently in focus
            #...
            
            # append command stuff to the log

    @classmethod
    def run(cls):
        ST.TerminalOutput.nl_print('loading...')
        cls.loop = True
        # start voice transcriber
        ST.VoiceInput.start_listening()
        # start main loop in new thread
        main_t = Thread(target=cls.main_loop, daemon=True)
        main_t.start()
        # start GUI
        ST.GUI_tk.run_GUI()         # must be called from main thread, will persist

    @classmethod
    def shutdown(cls):
        ST.TerminalOutput.nl_print('shutting down...')
        cls.loop = False
        ST.VoiceInput.stop_listening()
        for prog in cls.progs:
            prog.shutdown()
        ST.GUI.end_GUI()


#---------

def spawn_sub_program(program_object, name:str):
    ST.TerminalOutput.nl_print(f'starting sub_program: "{name}"')
    prog = program_object(name)                     # instatiate the object
    prog_id = prog.id
    progs.update({prog_id: prog})                   # add object to sub_progs list

def terminate_sub_program(id:str):
    prog = progs.get(id)
    prog.shutdown()
    progs.pop(id)

def check_if_waking(input):
    text = input.get('text')
    time = input.get('time')

    # [1] first validate input for command activation
    # A. validate that either the phrase contains a wake word, or it happened within the wake_timeout
    if ST.GeneralTools.match_keywords(('app_command_word', ), text):
        pass
    elif last_wake_time and ST.GeneralTools.validate_if_within_timeout(time, last_wake_time, wake_timeout):
        pass
    else:
        return
    
    # if all the above conditions are met, then set the wake time to now, and return True
    last_wake_time = datetime.now()
    return True

# check conditions, spawn commands
def check_spawn_commands(text):
    # [2] try getting action from input
    for command in input_command_reference:
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







#-------------------------------

if __name__ == "__main__":
    run()
    print('goodbye!')