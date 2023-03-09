from threading import Thread

import commands
import sub_programs

Coms = commands.coms

#-------------------------------

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
    Coms.end_core_procs()

def run():
    # start
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