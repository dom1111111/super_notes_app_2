"""
contains all classes needed to run the app
"""
from time import sleep
from datetime import datetime
from threading import Lock, Thread
from queue import Queue
from functools import wraps
from UI_scripts import stt, tts, play_rec_audio, GUI_tk
from external_scripts import number_tools, time_tools, word_tools

#-------------------------------
# UI Objects

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
        self._vox_in = stt.VoiceToText()
        self._vox_out = tts.ComputerVoice()
        self._audio_out = play_rec_audio.PlayAudio()
    
    #---------
    # voice-input methods

    @_vox_in_wrap
    def start_listening(self):
        """Start listening for voice phrases"""
        self._vox_in.start_listening()
    
    @_vox_in_wrap
    def stop_listening(self):
        """Stop listening for voice phrases"""
        self._vox_in.stop_listening()
    
    def get_voice_audio(self) -> bytes:
        """Get earliest audio phrase data, which can then be transcribed to text via `transcribe_voice_audio()`.
        This method is **blocking**"""
        self._vox_in.get_audio_phrase()
    
    def transcribe_voice_audio(self, audio_data:bytes, vocabulary:str, full_vocab:bool=False) -> str:
        """Transcribe phrase audio data (returned from `get_voice_audio()`) into text.
        `vocabulary` must be a single string, with the words separated by whitespace"""
        self._vox_in.transcribe_audio(audio_data, vocabulary, full_vocab)

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
    def nl_print(self, message):
        """Same as default `print()` function but with an extra line break!"""
        print('\n' + message)

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
# Command Objects

class Command:
    def __init__(self, name:str, function, keywords:tuple, *args:str):
        """
        This is the class for commands

        * `name` - the name of the command
        * `function` - the function to be called when the command is executed
        * `keywords` - a tuple of key words which make up the command's primary input requirement
        """
        #* `args` - any number of argument objects
        self.name = name
        self.function = function
        self.keywords = keywords
        self.args = args
        #self.persistent = persistent
        #self.response = ""

#-------------------------------
# App Core class

# aka Input to Command Executer
class AppCore:
    def __init__(self):
        self.active = False
        self.UI = TextAudioUI()

        self.wake_words = "computer"
        self.last_wake_time = None
        self.wake_timeout = 5                   # in seconds
        
        self.commands = []                      # stores all commands
        self.all_command_keywords = set()       # stores all command keywords - used for transcriber vocabulary
        
        self.current_cycle_input = None


    def _generate_command_keywords(self):
        """generate the `all_command_keywords` set from the existing commands in the `commands`"""
        self.all_command_keywords = {keyword for command in self.commands for keyword in command.keywords}  # nested set comprehension
        # MAKE THIS A DICT

    def _input_director(self):
        while self.active:
            # [1] check for input - restart loop if none
            input_audio = self.UI.get_voice_audio()                                 # this is blocking
            if not input_audio:
                continue
            input_time = datetime.now()
            input_text = self.UI.transcribe_voice_audio(input_audio, "computer")    # check that the input contains the wake_word(s)

            # [2] check if input meets wake condition (either has wake_words or within timeout)
            if input_text: # and self.wake_words in input_text:
                waking = True
                self.last_focus_time = input_time                                   # set last focus time to time of input
            elif self.last_focus_time and time_tools.validate_if_within_timeout(input_time, self.last_focus_time, self.focus_timeout):
                waking = True
            else:
                waking = False
            
            # [3] if waking
            if waking:
                input_text = self.UI.transcribe_voice_audio(input_audio, word_tools.get_keywords_str(all=True))
                if not input_text:
                    continue
                self.UI.nl_print(f'>>> Voice: "{input_text}"')
            
                # [4] check each command's condition
                for command_dict in input_command_reference:
                    # check the comand's condition
                    condition = command_dict.get('condition')
                    # if the condition passes, return the command
                    if condition:
                        print('got it!')
                        matched_command = command_dict
                        break

                # [5] if a command is returned, then do it!
                if command_dict:
                    self.last_focus_time = None                 # reset last focus time
                    name = command_dict.get('name')
                    self.UI.nl_print(f'doing command: {name}')
                    command = command_dict.get('command')
                    command()
            else:
                pass

    #---------

    def set_commands(self, commands):
        """set the app commands by supplying an itterable containing `Command` objects"""
        # add all items from the itterable argument to `self.commands`, which are `Command` objects
        self.commands = [c for c in commands if isinstance(c, Command)]
        self._generate_command_keywords()                       # generate the command keywords dict

    def run(self, main_prog):
        self.UI.nl_print('loading system...')
        self.active = True
        self.UI.start()                         # start UI
        self.UI.nl_print('started!')
        #self.UI.run_GUI()                      # start GUI     # must be called from main thread, will persist

    def shutdown(self):
        self.UI.nl_print('shutting down...')
        self.active = False
        self.UI.stop()
        #self.UI.end_GUI()
