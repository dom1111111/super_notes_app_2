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
# Command and Input Processing Classes and Functions

class Command:
    """
    A class to create command objects

    ---

    ## Attributes
    
    ### `name`: str
        A name to identify the command
    
    ### `input`: tuple   
        A tuple containing each input requirement. All items within can either be a string, a list, or another tuple.

        - the very first requirement in the tuple will be treated as the command's *keywords*. This is the first thing that will be looked for when seeing if the input matches the command.

        The items will also be treated differently depending on their content:
        
        * a string of a single word - the input must contain this word
        * a string with value 'NUMBER' - the input must contain any number words (ex: 'one', 'twenty six', etc.)
        * a string with value 'TIME' - same as NUMBER, but with the addition of time words ('minute', 'day', etc.)
        * a string with value 'OPEN' - can be anything! an open ended message, rather than a specific limited requirement. This will always be checked for last, after all other requirements have been found.
        * a tuple - the input must contain ANY of the items within the tuple (the first item found in input will be used as this value)
        * a list - the input must contain ALL of the items within the list
        
        ...

        - the items in tuples and lists can be any of the above, including more tuples and lists! So sub-requirements can be nested within requirements
        - if a tuple or list has a *single-item set* within it, the item value will be used as the overall req value if the requirement is met by the input
        
        ...

        example: 
        `['hello', 'cool', ('person', 'dog', 'cucumber'), 'TIME', {'greeting'}]` 
        - so this requirement will only be considered met if the input contains:
            'hello', 'cool', any of the words within the tuple ('person', 'dog', 'cucumber'), and any time words.
        If all are present in input, then the value of this requirement will be the set item value: 'greeting'.
        
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
        self.input = input
        self.func = func
        self.args = args
        self.output = output


class CommandAction:
    def __init__(self):
        pass


#------

def get_input_keywords(self):
    """get command keywords to use for transcriber vocabulary"""
    pass

def get_all_input_words(self):
    """get all requirement words to use for transcriber vocabulary"""
    pass

def does_input_match_command_keywords(user_input:str, command:Command):
    pass

def get_command_action_from_input(user_input:str, command:Command):
    """checks if user input meets a command's input requirements, 
    and if it does, returns a corresponding action"""

    user_input = user_input.replace(',', '')                        # remove all commas from input string
    user_input = user_input.split()                                 # split input string into list of single words
    
    def get_req_value(req:str|tuple):
        # All requirements have a type, content/condition, and value.
        # The type determines how the content/condition should be tested, 
        # and the value is a result of the condition being met or not.

        def get_data_from_req(req:str|tuple|list):
            # if the req is itterable, check if contains a *single item set*
            # if it does, this should be the value - and also must remove the item from the itterable
            try:
                v = [i for i in req if isinstance(i, set) and len(i)==1]    # create list made up of only one-item sets
                i = req.index(v[0])                                         # get index of the set
                cont = req[:i] + req[i+1:]                                  # remove the set from the itterable req
                v = v[0].pop()                                              # isolate the value within the set
            except:
                cont = req
                v = None
            # determine the requirement type by its value or data-type
            if req == 'NUMBER' or req == 'TIME' or req == 'OPEN':   # single string, special value type
                return req, None, None
            elif isinstance(req, tuple):                            # tuples represent ANY type
                return 'ANY', cont, v
            elif isinstance(req, list):                             # lists represent ALL type
                return 'ALL', cont, v
            else:                                                   # single string type
                return 'STR', cont, v

        r_type, r_content, r_value = get_data_from_req(req)

        value = None

        if r_type == 'STR':
            value = r_content if r_content in user_input else None
        elif r_type == 'NUMBER':
            pass
            #value = [x for x in user_input.split() if x in number_tools.get_all_number_words()]
            #value = pass
            # TRANSLATE INPUT TO NUMBERS FIRST!
        elif r_type == 'TIME':
            pass
            #('day', 'days', 'hour', 'hours', 'minute', 'minutes', 'second', 'seconds') + number_tools.get_all_number_words()
        elif r_type == 'OPEN':
            pass
        elif r_type == 'ANY':
            for sub_req in r_content:
                sub_val = get_req_value(sub_req)
                if sub_val:
                    value = sub_val
                    break
        elif r_type == 'ALL':
            value = True
            for sub_req in r_content:
                if not get_req_value(sub_req):
                    value = None
                    break

        value = r_value if r_value and value else value
        return value

    #------

    input_req_values = []
    
    for req in command.input:
        input_req_values.append(get_req_value(req))

    # IF THERE'S AN OPEN REQ, THEN ISOLATE ALL THE OTHER FOUND REQS FROM STRING, AND WHATEVER'S LEFT, WILL BE THE OPEN VALUE!

    if all(input_req_values):
        return 'action!'
        # generate action and return it!

def generate_command_action(command:Command, input_req_values:tuple):
    # add this to command runner:
    pass
    #result = command.func()
    #speak(message_pt1, result, message_pt2)

    """
    def _generate_action(self, func:Callable|str, args:tuple, output:str):
        # set function
        f = func
        if isinstance(func, str):
            str_func_map = {
                'SHUTDOWN': function,
            }
            f = str_func_map.get(func)
        # 
        
        ###
        def _generate_command_action(self, command):
            # add this to command runner:
            pass
            #result = command.func()
            return (message_pt1, result, message_pt2)
        ###
    """

#-------------------------------
# Core helper classes

class CommandActionRunner:
    def __init__(self, UI:TextAudioUI):
        pass

"""
class _ALT_voice_input_processor(self):
    pass
    # same as normal, but does full vocab transcription, so is much simpler, but slower
"""  

class VoiceInputCommandProcessor:
    def __init__(self, UI:TextAudioUI, commands:list[Command]):
        self._UI = UI
        self._transcriber = stt.Transcriber()
        self._wake_timer = time_tools.Timer(5, self._wake_timeout)      # keeps track of wakfulness in real time
        
        self._wakewords = 'commputer'
        self._all_command_keywords = self._generate_command_keywords()  # all command keywords - used for transcriber vocabulary
        
        self._current_input = []                                        # all of the current input for a single cycle
        self._current_command = None                                    # the name of command whose keywords have been matched

    #---------

    def _generate_command_keywords(self, ):
        """generate the `all_command_keywords` set from the existing commands in the `commands`"""
        return {keyword for command in self._commands for keyword in command['input']}  # nested set comprehension
        # MAKE THIS A DICT

    def _add_to_current_input(self, input_audio:bytes):
        self._current_input.append(
            {
                'audio':    input_audio,
                'text1':    None,
                'text2':    None
            }
        )

    def _reset_command_input(self):
        """resets current input cycle"""
        # self._wake_timer.stop()
        self._current_input.clear()
        self._current_command = None
    
    def _wake_start(self):
        self._wake_timer.start()
        # vvv should eventually be a visual colour indication of wakefullness -> something lights up when awake, and stops when timer runs out
        self._UI.nl_print('\n\n---waking!---')

    def _wake_timeout(self):
        self._reset_command_input()
        # AGAIN, replace with visual colour change or something
        self._UI.nl_print('wake timer ran out!')

    #---------

    def _validiate_input(self, input_audio:bytes, wakewords:str) -> bool:
        """Check if input audio contains wakeword(s) or is within wake timeout.
        Wakewords must be a single word or multiple seperated by whitespace"""
        if self._transcriber.transcribe(input_audio, wakewords):
            self._reset_command_input()
        elif self._wake_timer.is_active():
            pass
        else:
            return False
        return True

    def _transcribe_current_input_audio(self):
        """transcribe each phrase in current_input depending on stage in input cycle
        (either looking for all commands by keyword, or looking at a single command reqs)"""
        for phrase in self._current_input:
            # if the phrase has not yet been transcribed (within the corresponding text feild),
            # and no command has been found yet, then transcribe it using all command keywords as vocabulary
            if not self._current_command and not phrase['text1']:
                text = self._transcriber.transcribe(phrase['audio'], ' '.join(self._all_command_keywords))
                phrase['text1'] = text if text else '_'
            # but if a command has been found, then transcribe it using the current_command's input requirements as vocabulary
            elif self._current_command and not phrase['text2']:
                if 'OPEN' in current_command:
                    text = self._transcriber.transcribe(phrase['audio'])
                else:
                    text = self._transcriber.transcribe(phrase['audio'], get_command_req_vocab(current_command))
                phrase['text2'] = text if text else '_'

    #---------

    def get_current_input_text(self) -> str:
        t_key = 'text2' if self._current_command else 'text1'
        text = ''
        for phrase in self._current_input:
            if not self._current_command:
                text += phrase[t_key] + ', '
        return text
    
    def add_input_audio_get_action(self, input_audio:bytes, commands:list[Command]):
        self._add_to_current_input(input_audio)
        
        while True:
            self._transcribe_current_input_audio()

            if not self._current_command:
                for command in commands:
                    if does_input_match_command_keywords(self.get_current_input_text(), command):
                        self._current_command = command
                        continue
            else:
                action = get_command_action_from_input(self.get_current_input_text(), self._current_command)
                if action:
                    return action
            
            break


#-------------------------------
# App Core class

# aka Input-to-Command Executer
class AppCore:
    def __init__(self, commands:list[dict]):
        self._active = False
        self._commands = self._set_commands(commands)           # stores all commands

        self._UI = TextAudioUI()
        self._vox_proc = VoiceInputCommandProcessor(self._UI, self._commands)

    def _set_commands(self, commands:list[dict]):
        """set the app commands by supplying a list containing command dictionary objects"""
        # add all items from the `commands` argument to `self.commands` which are dictionaries
        self._commands = [c for c in commands if isinstance(c, dict)]

    #---------
    # methods for internal command actions

    def _shutdown(self):
        self._UI.nl_print('shutting down...')
        self._active = False
        self._UI.stop()
        #self._UI.end_GUI()

    #---------
    # main loop methods

    def _get_input(self):
        """wait for input, then return it"""
        return self._UI.get_voice_audio()        # this is blocking

    def _get_command_from_input(self, user_input):
        pass
    """
    def get_command_from_input(self, user_input:str, commands:list[Command]):
        for command in commands:
            action = get_command_action_from_input(user_input, command)
            if action:
                return action
    """
    
    def _do_command_action(self, action):
        pass
    # [3] if get an action back from command, run the command action (in seperate thread)

    def _main_loop(self):
        while self._active:
            user_input = self._get_input()
            com_action = self._get_command_from_input(user_input)
            if com_action:
                self._do_command_action(com_action)

    #---------

    def run(self):
        self._UI.nl_print('loading...')
        self._active = True
        self._UI.start()                        # start UI
        self._UI.nl_print('starting!')
        self._main_loop()




######################################
# CODE TO REVIEW
######################################

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