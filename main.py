from threading import Thread

import commands
import sub_programs

Coms = commands.coms

#-------------------------------

class Main():
    def __init__(self):

        # for voice input validation
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

    def main(self):
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
            return
        
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


def main_loop():
    while Coms.loop:
        # [1] check for input
        input = Coms.get_voice_input()

        if input:
            input_text = input.get('text')
            Coms.output_to_log(f'input: "{input_text}"')
            Coms.nl_print(f'input: "{input_text}"')

        # [2] Go through each sub_program from highest to lowest prioirty
        # if any use the input (return True), then end the current cycle and start over again
        for prog in Coms.sub_progs:
            response = prog.main(input)
            if response == 'done':
                Coms.terminate_sub_program(prog.name_id)
            elif response == True:
                break
            else:
                continue

        # append command stuff to the log

    # shutdown
    """
        def end_core_procs(self):
            self.nl_print('shutting down...')
            self.nl_print('ending voice input...')
            self.vox.stop_listening()
            sleep(1)
            self.nl_print('voice input now off')
            GUI.terminate_GUI()
    """

def run():
    # start
    """
    def start_core_procs(self):
        self.nl_print('loading voice input...')
        self.vox.start_listening()
        self.nl_print('voice input now active!')
    """
    # set the transcriber vocabulary
    Coms.loop = True
    Coms.spawn_sub_program(sub_programs.VoiceController, 'voice controller')    # launch the voice controller, which will check input for new commands
    Coms.start_core_procs()
    t = Thread(target=main_loop, daemon=True)
    t.start()
    Coms.run_GUI()

#-------------------------------

if __name__ == "__main__":
    run()
    print('goodbye!')