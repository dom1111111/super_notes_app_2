from threading import Thread, Lock, active_count
from queue import Queue
from datetime import datetime
from time import sleep
from os import path

import shared_resources as SR
#import programs_commands as PC


#-------------------------------

class Core():
    active = False

    progs = {}                  # active program objects
    main_prog_id = None
    current_prog_id = None

    last_focus_time = None
    focus_timeout = 5           # in seconds

    #---------
    
    @classmethod
    def spawn_program(cls, prog_object, make_focus:bool=False):
        # make sure that the program being spawned is a subclass of Parent Program class
        assert issubclass(prog_object, SR.PersistentProgram)
        SR.Terminal.nl_print(f'starting sub_program: "{prog_object.__name__}"')
        prog = prog_object()                    # instatiate the object
        prog_id = prog.id
        cls.progs.update({prog_id: prog})       # add object to sub_progs list
        if make_focus:
            cls.current_prog_id = prog_id       # update current program focus
        return prog_id

    @classmethod
    def terminate_program(cls, id:str):
        prog = cls.progs.get(id)
        prog.end()
        # reset current program focus if this program was the one in focus
        if cls.current_prog_id == id:
            cls.current_prog_id = None
    
    #---------

    @classmethod
    def _input_director(cls):
        while cls.active:
            # [1] check for input - restart loop if none
            input_audio = SR.VoiceInput.get_audio_phrase()      # this is blocking
            if not input_audio:
                sleep(0.01)
                continue
            input_time = datetime.now()
            input_text = SR.VoiceInput.transcribe_audio(input_audio, SR.WordTools.get_keywords_str('wake_words'))

            # [2] check if input meets focus condition (either has wake_words or within timeout)
            if input_text and SR.WordTools.match_keywords(('wake_words', ), input_text):
                in_focus = True
                cls.last_focus_time = input_time                # set last focus time to time of input
            elif cls.last_focus_time and SR.TimeTools.validate_if_within_timeout(input_time, cls.last_focus_time, cls.focus_timeout):
                in_focus = True
            else:
                in_focus = False
            
            # [3] if in focus, send input to main program, else send to currently in focus program (if there is one)
            if in_focus:
                prog = cls.progs.get(cls.main_prog_id)
                prog.give_input_audio(input_audio)
            elif cls.current_prog_id:
                prog = cls.progs.get(cls.main_prog_id)
                prog.give_input_audio(input_audio)

    @classmethod
    def run(cls, main_prog):
        SR.Terminal.nl_print('loading system...')
        cls.active = True
        SR.VoiceInput.start_listening()         # start voice transcriber
        Thread(target=cls._input_director, daemon=True).start()     # start loop is separate thread
        id = cls.spawn_program(main_prog)       # initiate main program
        cls.main_prog_id = id
        SR.Terminal.nl_print('started!')
        SR.GUI_tk.run_GUI()                     # start GUI     # must be called from main thread, will persist

    @classmethod
    def shutdown(cls):
        SR.Terminal.nl_print('shutting down...')
        cls.active = False
        SR.VoiceInput.stop_listening()
        for prog in cls.progs.values():
            cls.terminate_program(prog.id)
        SR.GUI.end_GUI()


#-------------------------------

class CommFuncs:
    def say_time():
        SR.VoiceOutput.say(f'it is currently {SR.TimeTools.get_current_time()}')

    def say_date():
        SR.VoiceOutput.say(f'it is {SR.TimeTools.get_current_date()}')


def get_command_from_input(txt_inpt:str):
    input_command_reference = [
        {
            'name':         'Shutdown',
            'condition':    SR.WordTools.match_keywords(('app' ,'shutdown'), txt_inpt),
            'command':      Core.shutdown
        },
        {
            'name':         'Get Time',
            'condition':    SR.WordTools.match_keywords(('time',), txt_inpt),
            'command':      CommFuncs.say_time     
        },
        {
            'name':         'Get Date',
            'condition':    SR.WordTools.match_keywords(('date',), txt_inpt),
            'command':      CommFuncs.say_date       
        },
        #{
        #    'name':         'New Note',
        #    'condition':    ('create', 'note'),
        #    'command':      func_wrap(self.spawn_program, PC.CreateNoteQuick, True)
        #},
        #{
        #    'name':         'Calculator',
        #    'condition':    ('calculate'),
        #    'command':      func_wrap(self.spawn_program, PC.Calculator, True)
        #},
        # undo
        # redo
    ]
    for command_dict in input_command_reference:
        # check the comand's condition
        condition = command_dict.get('condition')
        # if the condition passes, return the command
        if condition:
            print('got it!')
            return command_dict

#---------

class MainProgram(SR.PersistentProgram):
    def __init__(self):
        super().__init__("MAIN_PROG", self.main_loop)
        self.command_keyword_list_str = SR.WordTools.get_keywords_str(all=True)

    def main_loop(self):
        while self.active:
            # [1] check for input - restart loop if none
            input_audio = self._get_input_audio()
            if not input_audio:
                sleep(0.01)
                continue
            input_text = SR.VoiceInput.transcribe_audio(input_audio, self.command_keyword_list_str)
            if not input_text:
                continue

            SR.Terminal.nl_print(f'>>> Voice: "{input_text}"')
        
            # [2] check each command's condition
            command_dict = get_command_from_input(input_text)
            # if a command is returned, then do it!
            if command_dict:
                self.last_focus_time = None                 # reset last focus time
                name = command_dict.get('name')
                SR.Terminal.nl_print(f'doing command: {name}')
                command = command_dict.get('command')
                command()


#-------------------------------

if __name__ == "__main__":
    # either start main program here, or pass it as an argument to run
    Core.run(MainProgram)
    print('goodbye!')