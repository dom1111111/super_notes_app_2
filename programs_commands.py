from datetime import datetime
from time import sleep

import system_tools as ST

# eventually split up commands into multiple scripts, and import them into this??

#-------------------------------
# Calculator

class CountUp(ST.PersistentCommand):
    def __init__(self, name):
        ST.PersistentCommand.__init__(self, name, self.do)
        self.n = 0

    def do(self):
        self.output_print(self.n)
        self.n += 1
        sleep(1)

class Calculator(ST.PersistentCommand):
    def __init__(self):
        ST.PersistentCommand.__init__(name=self.__name__)
    
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