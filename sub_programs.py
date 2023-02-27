"""
This is a collection of classes to spawn "sub-program" objects.

All sub-program objects must include these features:
- a method called `main`, which will be called by the main loop repeadely until it's finished
    - this will be the sub-programs loop
- returns "done" when it is complete
- the `main` method accepts input (transcription) as its only argument (other than self of course)
    - even if it doesn't use input, it must accept it
- if it ends up using the input, it must return `True`, and if it doesn't, it must return `False`
"""
from datetime import datetime

import commands
from sub_apps import nodes

Nodes = nodes.ReadWriteNodes()
Coms = commands.coms

#-------------------------------
# Sub-Program Parent Class

class PersistentCommand:
    def __init__(self, name:str):
        self.name_id = name + '-' + datetime.now().strftime(Coms.time_str_format_1)
    
    def unpack_transcription(self, transcription):
        self.time = transcription.get('timestamp')
        self.audio_power = transcription.get('audio power')
        self.text = transcription.get('text')  

#-------------------------------
#-------------------------------
# Main App related sub-programs

class VoiceController(PersistentCommand):
    def __init__(self, name):
        super().__init__(name)

        # for voice input validation
        self.phrase_threshold = 0
        self.last_wake_time = None
        self.wake_timeout = 5       # in seconds

        # THIS SHOULD EVENTUALLY BE A JSON
        # with open('com_ref.json', 'w') as file:
        #     self.command_reference = json.loads(file)
        # Use this for now:
        self.command_reference = [
            {
                'name':         'new note',
                'conditions':   [(Coms.match_keywords, ('create', 'note'))],
                'command':      (Coms.spawn_sub_program, (CreateNoteQuick, 'new note'))
            },
            {
                'name':         'shutdown',
                'conditions':   [(Coms.match_keywords, ('exit', 'app'))],
                'command':      (Coms.end_loop, None)
            }
        ]

    def main(self, transcription:dict):
        # only run this function if transcription is not None
        if not transcription:
            return
        # get variables from input
        self.unpack_transcription(transcription)

        # [1] first validate input for command activation
        # A. validate that either the phrase contains a wake word, or it happened within the wake_timeout
        if Coms.match_keywords(('app_command_word', ), self.text):
            pass
        elif self.last_wake_time and Coms.validate_if_within_timeout(self.time, self.last_wake_time, self.wake_timeout):
            pass
        else:
            self.phrase_threshold = 0
            return
        # B. validate that the phrase's audio power is above the phrase threshold
        #if not audio_power > self.phrase_threshold:
        #    return False
        
        # if all the above conditions are met, then set the wake time to now, and continue
        self.last_wake_time = datetime.now()
        
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

                Coms.nl_print(f'starting command: {name}')
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
        return


#-------------------------------
# Nodes sub-programs

class CreateNoteQuick(PersistentCommand):
    def __init__(self, name):
        super().__init__(name)
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
