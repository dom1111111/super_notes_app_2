from threading import Thread, Lock
from queue import Queue
from datetime import datetime

import system_tools as ST
import programs_commands as PC

#-------------------------------

class Requests:
    def __init__(self):
        self.mutex = Lock()
        self.requests = []
    
    def add(self, source_id:int, func, args:tuple):
        # check request if it can be done
        
        
        request = {
            'id':   source_id,
            'func': func,
            'args': args
        }
        with self.mutex:
            self.requests.append(request)

    def get(self):
        with self.mutex:
            # return item value, and reset it to None
            return item

#-------------------------------

class MainController():
    def __init__(self):
        self.loop = False
        self.progs = []                     # should store active sub-program objects
        self.current_prog_focus = None
        
        self.requests = Queue()

        # for voice input validation
        self.last_wake_time = None
        self.wake_timeout = 5               # in seconds

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
                'command':      self.shutdown
            }
            # undo
            # redo
        ]

    #---------

    def spawn_sub_program(self, program_object, name:str):
        ST.nl_print(f'starting sub_program: "{name}"')
        prog = program_object(name)                     # instatiate the object
        self.sub_progs.append(prog)                     # add object to sub_progs list
        self.sub_progs.sort(key=lambda x: x.priority)   # sort sub_progs list by object attribute: "priority"

    def terminate_sub_program(self, id:str):
        for prog in self.sub_progs:
            if prog.id == id:
                i = self.sub_progs.index(prog)
                self.sub_progs.pop(i)
                break

    def check_if_waking(self, input_text):
        # get variables from input
        text = com.get_current_input_text()
        time = com.get_current_input_time()

        # [1] first validate input for command activation
        # A. validate that either the phrase contains a wake word, or it happened within the wake_timeout
        if com.match_keywords(('app_command_word', ), text):
            pass
        elif self.last_wake_time and com.validate_if_within_timeout(time, self.last_wake_time, self.wake_timeout):
            pass
        else:
            return
        
        # if all the above conditions are met, then set the wake time to now, and return True
        self.last_wake_time = datetime.now()
        return True

    # check conditions, spawn commands
    def check_spawn_commands(self):
        # [2] try getting action from input
        for command in self.command_reference:
            name = command.get('name')
            conditions = command.get('conditions')
            command = command.get('command')
            
            # check each of the comand's conditions - if any fail, then break the loop
            for condition in conditions:
                condition_func = condition[0]
                condition_arg = condition[1]
                passed = condition_func(condition_arg, self.text)
                if not passed:
                    break
            
            # if all of the conditions pass, then do the action
            if passed:
                func = command[0]
                args = command[1]

                com.nl_print(f'starting command: {name}')
                self.last_wake_time = None      # reset wake time

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
            input_package = ST.Vox.get_transcribed_phrase()
            if not input_package:
                continue
            input_text = input_package.get('text')
            
            ST.nl_print(f'input: "{input_text}"')

            # [2] run main program and pass it input
            main = self.main_program(input_package)
            # check if it uses input
            if main:
                continue

            # [3] if main program didn't use input, pass it to the program/command currently in focus
            #...
            


            # append command stuff to the log

    def request_loop(self):
        while self.loop:
            pass

    def run(self):
        ST.nl_print('loading...')
        self.loop = True
        # start voice transcriber
        ST.Vox.start_listening()
        # set the transcriber vocabulary
        # ...
        # start main loop and request loop in threads
        main_t = Thread(target=self.main_loop, daemon=True)
        req_t = Thread(target=self.request_loop, daemon=True)
        main_t.start()
        req_t.start()
        # start GUI
        ST.GUI_tk.run_GUI()         # must be called from main thread, will persist

    def shutdown(self):
        ST.nl_print('shutting down...')
        self.loop = False
        ST.Vox.stop_listening()
        ST.GUI_tk.terminate_GUI()


#-------------------------------

if __name__ == "__main__":
    mc = MainController()
    mc.run()
    print('goodbye!')