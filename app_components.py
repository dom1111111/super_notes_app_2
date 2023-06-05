"""
contains all classes needed to run the app
"""
from time import sleep
from datetime import datetime
from threading import Lock, Thread, Event
from queue import Queue
from functools import wraps
from typing import Callable
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
# Command class and methods

class CommandAction:
    def __init__(self):
        pass

class Command:
    """
    A class to create command objects

    ---

    ## Attributes
    
    ### `name`: str
        A name to identify the command
    
    ### `input`: tuple   
        A tuple containing a string for each input requirement.

        All requirements in the tuple must be strings, but certain ones will be treated differently depending on their value:
        * '' - a single string with a word which must be met. ex: 'start'.
        * 'KEY()' - the command keywords. Can hold a single or mutliple items. If multiple items, all must be met. **This should be the first requirement in the input tuple, and will be the first requirement that will be looked for**
        * 'ALL()' - represents multiple words or items (seperated by commas). all items inside the brackets must be met by the input.
        * 'ANY()' - any (at least one) of the items inside the brackets must be met by input.
        * 'NUMBER' - the same as a single string, but will be treated as an 'ANY()' with all number words ('one', 'twenty six', etc.).
        * 'TIME' - same as 'NUMBER' but with the addition of time words ('minute', 'day', etc.).
        * any of the above followed by '-> word1' will mean that if the requirement is met, its value will be 'word1'.
        otherwise, the value will will be whatever value is already there. the only reason to use this is if the requirement is used.
        * 'OPEN' - can be anything! basically an open ended message, rather than a specific limited requirement.
        This will always be checked for last, after all other requirements have been found.

        Also, any of these can be nested within each other.

        ex: `All(word1, word2, ANY(word1, word2), TIME) -> start` - so this is a single requirement which is only considered met if 
        input contains 'word1', 'word2', any of the words within the 'ANY()', and any time-related words

        another ex: `KEY()`
        
    ### `func`: Callable | str
        An object which encapsulates the command's main functionality or logic. 
        
        Should usually be a function, but can also be string which maps to an internal app function that would otherwise be unreachable:
        * 'SHUTDOWN': shuts down the app

    ### `args`: tuple
        The arguments which should be passed to the function.
        These can be mapped to the value of an input requirement with a string of the index number of the requirement surrounded by sqaure brackets.
        
        ex: `([2], 'hello')` - in this case, there are 2 arguments which will passed to the function:
        * the value of the third input requirement
        * a string with the value 'hello'

    ### `output`: str
        A message to be returned after the func is called.
        If 'FUNC' is within the string, then it will be replaced with the return value of func attribute.
        Like with args, if an input requirement index (ex: [1]) is within the string, then it will replaced with its value
    """
    def __init__(self, name:str, input:tuple, func:Callable|str, args:tuple=(), output:str=''):
        self.name = name
        self.input = self._generate_input_objects(input)
        self.action = self._generate_action(func, args, output)

    def _generate_input_objects(self, input_reqs:tuple[str]):
        """
        All requirements in the tuple must be strings, but certain ones will be treated differently depending on their value:
        * '' - a single string with a word which must be met. ex: 'start'.
        * 'KEY()' - the command keywords. Can hold a single or mutliple items. If multiple items, all must be met. **This should be the first requirement in the input tuple, and will be the first requirement that will be looked for**
        * 'ALL()' - represents multiple words or items (seperated by commas). all items inside the brackets must be met by the input.
        * 'ANY()' - any (at least one) of the items inside the brackets must be met by input.
        * 'NUMBER' - the same as a single string, but will be treated as an 'ANY()' with all number words ('one', 'twenty six', etc.).
        * 'TIME' - same as 'NUMBER' but with the addition of time words ('minute', 'day', etc.).
        * any of the above followed by '-> word1' will mean that if the requirement is met, its value will be 'word1'.
        otherwise, the value will will be whatever value is already there. the only reason to use this is if the requirement is used.
        * 'OPEN' - can be anything! basically an open ended message, rather than a specific limited requirement.
        This will always be checked for last, after all other requirements have been found.
        """

        def get_req_input_value(input:str, req:str):
            # 
            def process_multi_reqs(req_type:str, mutli_reqs:str):
                """this will process any input requirements which hold multiple items.
                `req_type` must be the all-caps word at the start of the multi_req, before the parentheses. ex: 'ALL' or 'ANY'"""
                value = []
                mutli_reqs = mutli_reqs.strip(f'{req_type}()').split(', ')
                for req in mutli_reqs:
                    value.append(get_req_input_value(input, req))
                return value

            # see if overridden value is provided, and split that off from the req
            if '->' in req:
                parts = req.split('-> ')
                req = parts[0]
                o_value = parts[1]
            else:
                o_value = None

            #
            if req.startswith('KEY'):
                value = process_multi_reqs('KEY', req)
            elif req.startswith('ALL'):
                pass
            elif req.startswith('ANY'):
                pass
            elif req == 'NUMBER':
                value = [x for x in input.split() if x in number_tools.get_all_number_words()]
                value = 
            elif req == 'TIME':
                ('days', 'hours', 'minutes', 'seconds') + number_tools.get_all_number_words()
            elif req == 'OPEN':
                pass
            else:
                pass

            return o_value if o_value else value


        def translate_str_req(req:str):
            if req.startswith('KEY'):
                r = req.strip('KEY()').split(', ')
                r = translate_str_req(r)
            elif req.startswith('ALL'):
                pass
            elif req.startswith('ANY'):
                pass
            elif req == 'NUMBER':
                number_tools.get_all_number_words()
            elif req == 'TIME':
                ('days', 'hours', 'minutes', 'seconds') + number_tools.get_all_number_words()
            elif req == 'OPEN':
                pass
            else:
                pass

        for req in input_reqs:
            translate_str_req(req)

            

    def _generate_action(self, func:Callable|str, args:tuple, output:str):
        # set function
        f = func
        if isinstance(func, str):
            str_func_map = {
                'SHUTDOWN': function,
            }
            f = str_func_map.get(func)
        # 
        """
        def _generate_command_action(self, command):
            # add this to command runner:
            pass
            #result = command.func()
            return (message_pt1, result, message_pt2)
        """

    #---------

    def get_input_keywords(self):
        pass

    def get_all_input_words(self):
        pass

#-------------------------------

class CommandRunner:
    def __init__(self):
        pass


#-------------------------------
# Core helper classes

class CommandInputProcessor:
    def __init__(self):
        self._current_input_text = None
    
    def get_command_from_input(self, input_text:str, commands:tuple[Command]):
        """return a command name from `commands` if `input_text` contains all its input requirements"""
        for command in commands:
            if command.is_match(input_text):
                return


"""
def _ALT_voice_input_processor(self):
    pass
    # same as normal, but does full vocab transcription, so is much simpler, but slower
"""

class VoiceInputCommandProcessor:
    def __init__(self, command_keywords:set, wake_timeout_func:Callable):
        self._all_command_keywords = command_keywords                   # all command keywords - used for transcriber vocabulary
        self._wake_timer = time_tools.Timer(5, self._generate_timeout_func(wake_timeout_func))  # keeps track of wakfulness in real time        
        self._transcriber = stt.Transcriber()

        self._current_command = None                                    # the name of command whose keywords have been matched
        self._current_input_audio = []                                  # all of the current input audio for a single cycle
        self._current_input_keyword_text = None                         # the transcribed text of all audio phrases in current_input, using all command keywords as vocabualry
        self._current_input_command_text = None                         # the transcribed text of all audio phrases in current_input, using current_command input requirements as vocabualry

    def _generate_timeout_func(self, timeout_func:Callable):            # the function the wake timer will call when the timer runs out
        def timeout():
            self.reset()
            timeout_func()
        return timeout

    #---------

    def reset(self):
        """resets current input cycle"""
        #self._wake_timer.stop()
        self._current_input_audio.clear()
        self._current_input_text = None
        self._current_command = None

    def get_current_input_text(self) -> str:
        return self._current_input_text
    
    #---------
    
    def validiate_input(self, input_audio:bytes, wakewords:str) -> bool:
        """Check if input audio contains wakeword(s) or is within wake timeout.
        Wakewords must be a single word or multiple seperated by whitespace"""
        if self._transcriber.transcribe(input_audio, wakewords):
            self.reset()
        elif self._wake_timer.is_active():
            pass
        else:
            return False
        # reset wake timer for every valid/waking phrase (iow: timer should only run out if no new phrases come in before the timeout)
        self._wake_timer.start()
        return True

    def transcribe_add_input(self, input_audio:bytes):
        """transcribe input audio, and add it to `current_input_audio` and `current_input_text`.
        If the wakeword system is used, `input_audio` value should be validated (`validate_input`) before passing to this method"""     
        # transcribe input
        if not self._current_command:                           # use all command keywords as vocabulary if no command has been found yet
            transcription = self._transcriber.transcribe(input_audio, ' '.join(self._all_command_keywords))
        else:                                                   # use the current_command's input requirements as vocabulary if command has been found
            # full vocab transcription should be used only if one of the args is open ended!
            transcription = self._transcriber.transcribe(input_audio, )
        input_text = transcription if transcription else '_'    # if transcriber doesn't return anything, then text value should be '_'
        self._current_input_audio.append(input_audio)           # add audio to current_input_audio
        self._current_input_text += input_text + ', '           # add transcribed text followed by a comma to current_input_text

    def check_for_command_keywords(self):
        pass

    
    while True:
        # check if input contains all of the command's keywords
        # keywords with multiple options (should be a tuple of strings) only need one of the words to be matched

        # check if 
        if not self._current_command:
            # check if the current input matches a command, or meets all of the current_command's requirements
            for command in self._commands:
                def check(req):
                    if isinstance(req, tuple) and any(word for word in req if word in self._current_input_text):
                        return True
                if all(check(req) for req in command['input']):
                    return command['name']
        break

    # def add_input_get_command
        # """Add input audio, and return a command if all currently added input meets the command's input requirements."""

    # THIS IS THE MAIN METHOD FOR FINDING COMMAND FROM INPUT
    # CAN BE USED WITH ANY VOICE OR TEXT PROCESSOR
  
        """
            if self._current_command

                if a command is matched from all commands:

                    set current command

                    check through all current input and transcribe (the for loop function, made up up of other smaller commands)

                    continue! (> go back to start of loop to transcribe the phrases based on reqs)

		        break

            else (is current_command):

                if command has all its reqs matched:

                    return command['name']
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
        #self._voice = VoiceInputCommandProcessor()

    def _generate_command_keywords(self):
        """generate the `all_command_keywords` set from the existing commands in the `commands`"""
        return {keyword for command in self._commands for keyword in command['input']}  # nested set comprehension
        # MAKE THIS A DICT

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
            #if 
            # vvv should eventually be a visual colour indication of wakefullness -> something lights up when awake, and stops when timer runs out
            self._UI.nl_print('\n\n---waking!---')

            # check if input has a command
                # if yes, pass
                # if not, continue
            
            # [3] run the command (in seperate thread)

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
