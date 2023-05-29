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
    
    def get_voice_audio(self, no_wait:bool=False) -> bytes:
        """Get earliest audio phrase data, which can then be transcribed to text via `transcribe_voice_audio()`.
        * This method is **blocking** unless `no_wait` arg is `True`"""
        return self._vox_in.get_audio_phrase(no_wait)
    
    def transcribe_voice_audio(self, audio_data:bytes, vocabulary:str='') -> str:
        """Transcribe phrase audio data (returned from `get_voice_audio()`) into text.
        `vocabulary` must be a single string, with the words separated by whitespace.
        If vocabulary is not provided, then the transcriber will use entire language vocabulary, which will typically take longer"""
        return self._vox_in.transcribe_audio(audio_data, vocabulary)

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

#-------------------------------
# App Core class

# aka Input to Command Executer
class AppCore:
    def __init__(self):
        self._active = False
        self._UI = TextAudioUI()
        self._commands = []                     # stores all commands
        self._all_command_keywords = set()      # stores all command keywords - used for transcriber vocabulary

        self._wake_words = "computer"
        self._wake_timer = time_tools.Timer(5, self._wake_timer_func)
        self._current_input = []                # stores all of the current input audio for a single cycle
        self._current_command = None

    def _generate_command_keywords(self):
        """generate the `all_command_keywords` set from the existing commands in the `commands`"""
        self._all_command_keywords = {keyword for command in self._commands for keyword in command['input']}  # nested set comprehension
        # MAKE THIS A DICT

    def _wake_timer_func(self):
        self._UI.nl_print('---input listener timer ran out!---', '\n', '\n')

    def _add_current_input(self, text:str, audio:bytes, time:datetime=datetime.now()):
        self._current_input.append(
            {
                'time':     time,
                'audio':    audio,
                'text':     text,
            }
        )

    #---------

    # add this to command runner:
    def command_action():
        pass
        #result = command.func()
        #speak(message_pt1, result, message_pt2)


    def _text_input_director(self):
        pass

    def _voice_input_director(self):
            # [1] wait for input
            input_audio = self._UI.get_voice_audio()        # this is blocking
            input_time = datetime.now()

            # [2] check if input is valid (has wakeword or is within wake timeout)
            if self._wake_words in self._UI.transcribe_voice_audio(input_audio, self._wake_words):
                self._current_input.clear()                 # if wakeword is said, reset current input,
                self._current_command = None                # and reset current_command
            elif self._wake_timer.is_active():
                pass
            else:
                # send to any other possible command objects (if that's still a thing)
                return
            # reset wake timer for every valid/waking phrase (iow: timer should only run out if no new phrases come in before the timeout)
            self._UI.nl_print('---waking!---')
            # ^ should eventually be a visual colour indication of wakefullness -> something lights up when awake, and stops when timer runs out
            self._wake_timer.start()
        

        # > probably should put all special string symbol functionality into a big transcribing method

            # [3] transcribe phrase input contains command keywords
            input_text = self._UI.transcribe_voice_audio(input_audio, ' '.join(self._all_command_keywords))
            if not input_text:
                return
            self._add_current_input(input_text, input_audio, input_time)
            self._UI.nl_print(f'    [{input_time}] Voice: "{input_text}"')
        

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

            """
            for command_dict in input_command_reference:
                # check the comand's condition
                condition = command_dict.get('condition')
                # if the condition passes, return the command
                if condition:
                    print('got it!')
                    matched_command = command_dict
                    break
            """
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


    #---------

    def set_commands(self, commands:list|tuple):
        """set the app commands by supplying an itterable containing command dictionary objects"""
        # add all items from the `commands` argument to `self.commands` which are dictionaries
        self._commands = [c for c in commands if isinstance(c, dict)]
        self._generate_command_keywords()                       # generate the command keywords dict

    def run(self):
        self._UI.nl_print('loading...')
        self._active = True
        self._UI.start()                        # start UI
        self._UI.nl_print('starting!')
        while self._active:
            self._voice_input_director()

    def shutdown(self):
        self._UI.nl_print('shutting down...')
        self._active = False
        self._UI.stop()
        #self._UI.end_GUI()
