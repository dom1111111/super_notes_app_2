from threading import Thread
from queue import Queue

#-------------------------------

# Program Parent Class
class PersistentProgram:
    def __init__(self, name:str, program_function):
        """
        This is the parent class for programs. All programs should inherit this class.

        Arguments:
        * `name` is for the name of the program; should be a string
        * `program_function` is the main program function, which will be run in a loop and in a new thread. 
        If the function is not meant to be looped, then `self.active` should be set to `False` at the end of the function
        """
        self.name = name
        self.user_input = Queue()
        self.active = True
        # start command thread:
        def program_function_loop():
            while self.active:
                program_function()
        Thread(target=program_function_loop, daemon=True).start()

    #---------

    def give_input(self, i):
        """
        `i` should be a string or audio data bytes
        """
        self.user_input.put(i)

    def end(self):
        self.active = False


#-------------------------------
# Calculator

"""
class Calculator(ST.PersistentCommand):
    def __init__(self):
        ST.PersistentCommand.__init__(self.__name__, self.calculate)
        self.vocabulary = ST.NUMBER_WORDS
    
    def calculate(self):
        ST.GUI.output_to_mainview('Welcome to Calculator!')
        input_audio = self.get_input_audio()

        # output all the stuff to GUI
        # request input text
        # check if it contains any numbers or operators
            # convert text to symbols
            # request output for the symbols to the screen
            # if word is "equals" (or "evaulate", etc.), then calculate expression and send further output
"""    

#-------------------------------
# Nodes sub-programs

"""
class CreateNoteQuick(ST.PersistentCommand):
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