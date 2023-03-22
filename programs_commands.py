from datetime import datetime
from time import sleep

from queue import Queue
from threading import Thread, Lock

import commands

# eventually split up commands into multiple scripts, and import them into this??

#-------------------------------

# IF NAME IS NOT NEEDED, THEN CONVERT TO DICT, WHERE KEY IS CONDITION, AND VALUE IS COMMAND

command_reference = {
    (Coms.match_keywords, ('create', 'note')):      CreateNoteQuick,
    (Coms.match_keywords, ('exit', 'app')):         Coms.end_loop
}

command_reference = [
    {
        'name':         'New Note',
        'conditions':   [(Coms.match_keywords, ('create', 'note'))],
        'command':      CreateNoteQuick
    },
    {
        'name':         'Calculator',
        'conditions':   [(Coms.match_keywords, ('create', 'note'))],
        'command':      Calculator
    },
    {
        'name':         'Shutdown',
        'conditions':   [(com.match_keywords, ('exit', 'app'))],
        'command':      Coms.end_loop
    }

    # undo

    # redo
]


#-------------------------------
# Sub-Program Parent Class

class SingleItemContainer:
    def __init__(self):
        self.__mutex = Lock()
        self.__item = None
    
    def put(self, data):
        with self.__mutex:      # better to use `with` (context manager), than `acquire` and `release` for locks
            self.__item = data

    def get(self):
        with self.__mutex:
            # return item value, and reset it to None
            item = self.__item
            self.__item = None  
            return item


class PersistentCommand:
    def __init__(self, name:str, command_function):
        self.time_id = datetime.now().strftime(Coms.time_str_format_1)
        self.name = name
        self.vocabulary = None
        self.GUI_code = None
        self.__user_input = SingleItemContainer()
        self.__active = True
        #self.__suspended = True

        self.command_function = command_function
        # start command thread
        t = Thread(target=self.__run_command, daemon=True)
        t.start() 
    
    def __run_command(self):
        self.command_function()
        # request to shut down this command
        #self.__active = False

    #---------

    def give_input(self, input_data):
        # check to make sure right type of data? - maybe implement a input_data object class?
        self.__user_input.put(input_data)

    #def suspend_toggle(self):
    #    self.__suspended = not self.__suspended

    def end(self):
        self.__active = False

    #---------

    def get_input(self):
        self.__user_input.get()

    def __make_request(self, func, args):
        request = {
            'id':   self.time_id,
            'func': func,
            'args': args
        }
        # requests_q.put(request)


#-------------------------------


#-------------------------------
#-------------------------------
# Calculator

class CountUp(PersistentCommand):
    def __init__(self, name):
        PersistentCommand.__init__(self, name, self.do)
        self.n = 0

    def do(self):
        self.output_print(self.n)
        self.n += 1
        sleep(1)

class Calculator(PersistentCommand):
    def __init__(self):
        PersistentCommand.__init__(name=self.__name__)
    
    def do(self):
        pass
        # output all the stuff to GUI
        # request input text
        # check if it contains any numbers or operators
            # convert text to symbols
            # request output for the symbols to the screen
            # if word is "equals" (or "evaulate", etc.), then calculate expression and send further output
        

#-------------------------------
# Nodes sub-programs

"""
class CreateNoteQuick(PersistentCommand):
    def __init__(self, name):
        super().__init__(name, 4)
        self.text_lines = [] 

    def main(self, transcription:dict):
        # only run this function if transcription is not None
        if not transcription:
            return
        # get variables from input
        self.unpack_transcription(transcription)
    
        # if end word(s) was not said, then append text to list, and return
        if not Coms.match_keywords(('end','note'), self.text):
            self.text_lines.append(self.text)
            Coms.output_to_main_view(self.text)
        # otherwise, write the note, and return 'done'
        else:
            Nodes.create_node(content=self.text_lines)
            Coms.nl_print('created note!')
            return 'done'
"""