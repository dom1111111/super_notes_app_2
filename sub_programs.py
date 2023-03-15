from datetime import datetime
import commands
import nodes

Nodes = nodes.ReadWriteNodes()
Coms = commands.coms

#-------------------------------
# Sub-Program Parent Class

class PersistentCommand:
    def __init__(self, name:str, priority:int):
        self.id = datetime.now().strftime(Coms.time_str_format_1)
        self.name_id = name
        self.priority = priority

    def unpack_transcription(self, transcription):
        self.time = transcription.get('timestamp')
        self.audio_power = transcription.get('audio power')
        self.text = transcription.get('text')  

#-------------------------------
#-------------------------------
# Nodes sub-programs

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
