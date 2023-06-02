"""
contains all classes needed to run the app
"""
from time import sleep
from datetime import datetime
from threading import Lock, Thread, Event
from queue import Queue
from functools import wraps
from UI_scripts import stt, tts, play_rec_audio, GUI_tk
from external_scripts import number_tools, time_tools, word_tools

#-------------------------------
# UI classes

class SharedResourceWrapper:
    def __init__(self):
        self.mutex = Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.mutex:
                result = func(*args,**kwargs)
            return result
        return wrapper

class TextAudioUI:
    """
    This is a voice and text based user interface. 
    Includes all needed methods for voice and text input and output.
    All methods are thread safe.
    """
    _vox_in_wrap = SharedResourceWrapper()
    _vox_out_wrap = SharedResourceWrapper()
    _audio_out_wrap = SharedResourceWrapper()
    _terminal_wrap = SharedResourceWrapper()
    _TUI_wrap = SharedResourceWrapper()

    def __init__(self):
        self._vox_in = stt.PhraseDetector()
        self._vox_out = tts.ComputerVoice()
        self._audio_out = play_rec_audio.PlayAudio()
    
    #---------
    # voice-input methods

    @_vox_in_wrap
    def start_listening(self):
        """Start listening for voice phrases"""
        self._vox_in.start_stream()
    
    @_vox_in_wrap
    def stop_listening(self):
        """Stop listening for voice phrases"""
        self._vox_in.stop_stream()
    
    def get_voice_audio(self, no_wait:bool=False) -> bytes:
        """Get earliest audio phrase data, which can then be transcribed to text via `transcribe_voice_audio()`.
        * This method is **blocking** unless `no_wait` arg is `True`"""
        return self._vox_in.get_audio(no_wait)

    #---------
    # voice-output methods

    @_vox_out_wrap
    def say(self, message:str, wpm:int=200):
        """Play back computer generated voice audio of a given string message in a sperate thread (non-blocking).
        `wpm` is an optional argument for speaking speed (words per minute). Default value is `200`"""
        self._vox_out.say(message, wpm)
    
    @_vox_out_wrap
    def shutup(self):
        """Stop any currently playing computer voice audio"""
        self._vox_out.shutup()

    #---------
    # general audio output methods

    @_audio_out_wrap
    def play_audio_file(self, path:str):
        """Start playing a wav audio file in a seperate thread (non-blocking)"""
        self._audio_out.play(path)

    @_audio_out_wrap
    def pause_resume_audio(self):
        """Pause audio if it's playing, and resume audio if it's paused"""
        self._audio_out.pause_resume()
    
    @_audio_out_wrap
    def stop_audio(self):
        """Stop audio playback completely. Any further audio playback must be re-initiated with another call to `play_file()`"""
        self._audio_out.stop()

    #---------
    # terminal output methods

    @_terminal_wrap
    def nl_print(self, *message):
        """Same as default `print()` function but with an extra line break!"""
        print('\n', *message)

    #---------
    # text UI methods

    #start_GUI = GUI_tk.run_GUI
    #end_GUI = GUI_tk.terminate_GUI
    #output_to_mainview = __wrap(GUI_tk.append_to_mainview)
    #clear_mainview = __wrap(GUI_tk.clear_mainview)

    #---------
    # class convenience methods

    def start(self):
        """Start running all of the UI components"""
        self.start_listening()

    def stop(self):
        """Stop running all of the UI components"""
        self.stop_listening()
        self.stop_audio()
        self.shutup()

#-------------------------------
# Command convinience functions

class Command:
    def __init__(self, name:str, input_keywords:list, input_args:list, output:str, func, args:tuple=None):
        self.name = name
        self.input_kw = input_keywords
        self.input_args = input_args
        self.func = func
        self.args = args
        self.output = output

def create_command_dict(name:str, input:list, func, args:tuple, output:str):
    """
    return a dictionary in the correct command format

        `name`: a string of a name to identify the command
        
        `input`: a list containing strings of each command input component or requirement. 
        Input requirements will be made up of both *keywords* and *arguments*.
        Keywords are words used to identify commands 
        Acceptable string values:
                
                - a single lowercase word = a core command keyword
                - njj
        
        `func`: a function or callable object which will be run if all command requirements are met during an input cycle.
        Is essentially the command's main action or logic.
        Alternatively, `func` can be or a special all uppercase string which maps to an internal function.
        
            - 
    """
    return {
        'name':     name,
        'input':    input,
        'function': func,
        'args':     args,
        'output':   output
    }


#-------------------------------
# Core helper classes

class TextInputCommandProcessor:
    def __init__(self, UI:TextAudioUI, commands:list):
        pass

"""
def _ALT_voice_input_processor(self):
    pass
    # same as normal, but does full vocab transcription, so is much simpler, but slower
"""

class VoiceInputCommandProcessor:
    def __init__(self, commands:list, wake_timeout_func):
        self._transcriber = stt.Transcriber()
        self._commands = commands
        self._all_command_keywords = self._generate_command_keywords()  # all command keywords - used for transcriber vocabulary

        self._current_input_audio = []                                  # all of the current input audio for a single cycle
        self._current_input_text = None                                 # the transcribed text of all input phrases in current_input
        self._current_command = None                                    # the name of command whose keywords have been matched
        
        def timeout_func():                                             # the function the wake timer will call when the timer runs out
            self._reset_current_cycle()
            wake_timeout_func()
        
        self._wake_timer = time_tools.Timer(5, timeout_func)            # keeps track of wakfulness in real time

    def _generate_command_keywords(self):
        """generate the `all_command_keywords` set from the existing commands in the `commands`"""
        self._all_command_keywords = {keyword for command in self._commands for keyword in command['input']}  # nested set comprehension
        # MAKE THIS A DICT

    def _reset_current_cycle(self):
        #self._wake_timer.stop()
        self._current_input_audio.clear()
        self._current_input_text = None
        self._current_command = None

    #---

    """
    def _generate_command_action(self, command):
        # add this to command runner:
        pass
        #result = command.func()
        #speak(message_pt1, result, message_pt2)
    """

    #---------

    def get_current_input_text(self) -> str:
        return self._current_input_text
    
    def validiate_input(self, input_audio:bytes, wakewords:str):
        """Check if input audio contains wakeword(s) or is within wake timeout.
        Wakewords must be a single word or multiple seperated by whitespace"""
        if self._transcriber.transcribe(input_audio, wakewords):
            self._reset_current_cycle()
        elif self._wake_timer.is_active():
            pass
        else:
            return False
        # reset wake timer for every valid/waking phrase (iow: timer should only run out if no new phrases come in before the timeout)
        self._wake_timer.start()
        return True

    def add_input_get_command(self, input_audio:bytes):
        """Add input audio, and return a command if all currently added input meets the command's input requirements.
        If the wakeword system is used, `input_audio` value should be validated (`validate_input`) before passing to this method"""     
        # transcribe input
        if not self._current_command:                           # use all command keywords as vocabulary if no command has been found yet
            transcription = self._transcriber.transcribe(input_audio, ' '.join(self._all_command_keywords))
        else:                                                   # use the current_command's input requirements as vocabulary if command has been found
            transcription = self._transcriber.transcribe(input_audio, )
        input_text = transcription if transcription else '_'    # if transcriber doesn't return anything, then text value should be '_'
        self._current_input_audio.append(input_audio)           # add audio to current_input_audio
        self._current_input_text += input_text + ', '           # add transcribed text followed by a comma to current_input_text

        

        while True:
            if not self._current_command:
                # [4] check if the current input matches a command, or meets all of the current_command's requirements
                for command in self._commands:
                    def check(req):
                        if isinstance(req, tuple) and any(word for word in req if word in self._current_input_text):
                            return True
                    if all(check(req) for req in command['input']):
                        return command['name']
                    
        """
                if a command is matched from all commands:

                    set current command

                    check through all current input and transcribe (the for loop function, made up up of other smaller commands)

                    continue! (> go back to start of loop to transcribe the phrases based on reqs)

		        break

            else (is current_command):

                if command has all its reqs matched:

                    return command['name']
        """


        
        # [4] see if current_input meets the input requirements of a command in the `commands` list
        """
        all_current_input_text = {text for input in self._current_input for text in input['text'].split()}
        self._UI.nl_print(f'    all_current_input_text: "{all_current_input_text}"')
        input_command_word_intersection = self._all_command_keywords.intersection(all_current_input_text)
        self._UI.nl_print(f'    input_command_word_intersection: "{input_command_word_intersection}"')
        """
        all_current_input_text = ' '.join([input['text'] for input in self._current_input])
        self._UI.nl_print(f'    all_current_input_text: "{all_current_input_text}"')
        input_command_word_intersection = [word for word in self._all_command_keywords if word in all_current_input_text]
        self._UI.nl_print(f'    input_command_word_intersection: "{input_command_word_intersection}"')
        
        # > if you use the keyword dictionary, (rather than set), then you need one dictionary for synonyms (this will be the one used for transcription!)
        # which point to another dictionary's key (which is the keyword), whose value will contain the command!

        # [5]
        # if a command is returned, then do it!
        """
        if command_dict:
            self._last_wake_time = None                 # reset last wake time
            name = command_dict.get('name')
            self._UI.nl_print(f'doing command: {name}')
            command = command_dict.get('command')
            command()
        """


class CommandRunner:
    def __init__(self, UI:TextAudioUI):
        pass


#-------------------------------
# App Core class

# aka Input to Command Executer
class AppCore:
    def __init__(self):
        self._active = False
        self._UI = TextAudioUI()
        self._commands = []                     # stores all commands

    def _generate_command_action(self, command):
        # add this to command runner:
        pass
        #result = command.func()
        #speak(message_pt1, result, message_pt2)

    #---------

    #---------

    def _main_loop(self):

        # object for voice processor
        # object for command doer?

        while self._active:
            # [1] wait for input
            input_audio = self._UI.get_voice_audio()        # this is blocking

            # [2] validate input
            if 
            # vvv should eventually be a visual colour indication of wakefullness -> something lights up when awake, and stops when timer runs out
            self._UI.nl_print('\n\n---waking!---')

    #---------

    def set_commands(self, commands:list|tuple):
        """set the app commands by supplying an itterable containing command dictionary objects"""
        # add all items from the `commands` argument to `self.commands` which are dictionaries
        self._commands = [c for c in commands if isinstance(c, dict)]
        #self._generate_command_keywords()                       # generate the command keywords dict

    def run(self):
        self._UI.nl_print('loading...')
        self._active = True
        self._UI.start()                        # start UI
        self._UI.nl_print('starting!')
        self._main_loop()

    def shutdown(self):
        self._UI.nl_print('shutting down...')
        self._active = False
        self._UI.stop()
        #self._UI.end_GUI()
