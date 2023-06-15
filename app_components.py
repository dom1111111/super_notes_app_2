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
            - this cannot have a {set} value, or any special string values (NUMBER, TIME, OPEN)
        
        The items will also be treated differently depending on their content:
        
        * a string of a single word - the input must contain this word
        * a string with value 'NUMBER' - the input must contain any number words (ex: 'one', 'twenty six', etc.)
        * a string with value 'TIME' - same as NUMBER, but with the addition of time words ('minute', 'day', etc.)
        * a string with value 'OPEN' - can be anything! an open ended message, rather than a specific limited requirement. This will always be checked for last, after all other requirements have been found.
        * ...
        * a tuple - the input must contain ANY of the items within the tuple (the first item found in input will be used as this value)
        * a list - the input must contain ALL of the items within the list
            - the items in tuples and lists can be any of the above (including more tuples and lists), **except** an OPEN!
                - So sub-requirements can be nested within requirements
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
        self.input = self._get_input_reqs_data(input)
        self.func = func
        self.args = args
        self.output = output

        self.keyword_input_vocab, self.all_input_vocab = self._get_input_req_words(input)

    @staticmethod
    def _get_input_req_words(input_reqs:tuple) -> str:
        """get both the input requirement keywords, and all the rest of the words, to use for transcriber vocabulary"""
        keywords = []
        words = []

        def add_words_from_req(req):
            if isinstance(req, str):
                if req == 'NUMBER':
                    words.extend(word_tools.NUMBER_WORDS)
                elif req == 'TIME':
                    words.extend(word_tools.TIME_WORDS + word_tools.NUMBER_WORDS)
                elif req == 'OPEN':
                    pass
                else:
                    words.append(req)
            elif isinstance(req, tuple) or isinstance(req, list):   # should only be tuple or list. sets should be ignored
                for r in req:
                    add_words_from_req(r)

        for n, req in enumerate(input_reqs):
            add_words_from_req(req)
            if n == 0:                              # for the first req, copy the initial words from `words` list into `keywords`
                keywords.extend(words)

        # remove duplicate words (by turning into set), and join into single string
        return ' '.join(set(keywords)), ' '.join(set(words))   

    @staticmethod
    def _get_input_reqs_data(input_reqs:tuple) -> tuple:
        """return a tuple of three-item-tuples (type, content, value) for each input requirement"""
        
        def get_req_data(req:str|tuple|list) -> tuple:
            # if the req is itterable, check if contains a *single item set*
            # if it does, this should be the value - and also must remove the item from the itterable
            try:
                val = [i for i in req if isinstance(i, set) and len(i)==1]  # create list made up of only one-item sets
                i = req.index(val[0])                                       # get index of the set
                cont = req[:i] + req[i+1:]                                  # remove the set from the itterable req
                val = val[0].pop()                                          # isolate the value within the set
            except:
                cont = req
                val = None
            # determine the requirement type by its value or data-type
            if req == 'NUMBER' or req == 'TIME' or req == 'OPEN':           # single string, special value type
                return (req, None, None)
            elif isinstance(req, tuple):                                    # tuples represent ANY type
                cont = tuple(get_req_data(sub_req) for sub_req in req)      # further convert any nested requirements
                return ('ANY', cont, val)
            elif isinstance(req, list):                                     # lists represent ALL type
                cont = tuple(get_req_data(sub_req) for sub_req in req)      # further convert any nested requirements
                return ('ALL', cont, val)
            else:                                                           # single string type
                return ('STR', cont, val)
        
        return tuple(get_req_data(r) for r in input_reqs) 

    @staticmethod
    def _get_input_req_value(req_type:str, req_content:str|tuple|list, user_input:list[str|int|float]):
        """Get the initial value of a single input requirement based its type and content, and on a list of user input items"""
        value = None

        def get_sub_values(r_content:tuple) -> tuple:
            # sub_req[0] and sub_req[1] is type and content respectively
            return tuple(Command._get_input_req_value(sub_req[0], sub_req[1], user_input) for sub_req in r_content)

        if req_type == 'STR':
            value = req_content if req_content in user_input else None
        elif req_type == 'NUMBER':
            nums = tuple(x for x in user_input if (isinstance(x, int) or isinstance(x, float)))
            value = nums[0] if nums else None       # only return the first instance of a number
        elif req_type == 'TIME':
            times = tuple(x for x in user_input if isinstance(x, ,,,))
            value = times[0] if times else None     # only return the first instance of a time
        elif req_type == 'OPEN':
            value = 'OPEN'                          # this will be processed outside of this method, so just have 'OPEN' as value
        elif req_type == 'ANY':
            sub_vals = get_sub_values(req_content)
            value = sub_vals[0] if any(sub_vals) else None
        elif req_type == 'ALL':
            sub_vals = get_sub_values(req_content)
            value = sub_vals if all(sub_vals) else None

        return value

    #------

    def get_keyword_req_value(self, user_input:str) -> tuple:
        """returns a tuple of values for command's keyword input requirement, based on user input"""
        usr_ipt_items = word_tools.get_words_only(user_input)                   # get a list with all words or numbers in user input
        return self._get_input_req_value(self.input[0], usr_ipt_items)          # keyword req is first item 

    def get_all_req_values(self, user_input:str) -> list:
        """returns a tuple of values for all command's input requirements, based on user input"""
        usr_ipt_items = word_tools.get_words_only(user_input)                   # get a list with all words or numbers in user input
        req_values = []

        for req in self.input:
            value = self._get_input_req_value(req[0], req[1], usr_ipt_items)
            # sub_req[0] and sub_req[1] is type and content respectively
            if value:
                if req[0] in ('STR', 'NUMBER', 'TIME', 'OPEN', 'ANY'):
                    usr_ipt_items.remove(value)
                elif req[0] == 'ALL':
                    for sub_val in value:
                        usr_ipt_items.remove(sub_val)
                
                # ADD THIS: value = r_value if r_value and value else value
                """
                for i, req in enumerate(self.input):
                    # if an value was specified in input, then override it
                    if req[2]:
                        req_values[i] = req[2]
                """
            req_values.append(value)

        # IF THERE'S AN OPEN REQ, THEN ISOLATE ALL THE OTHER FOUND REQS FROM STRING, AND WHATEVER'S LEFT, WILL BE THE OPEN VALUE!
        # ONLY DO IF ALL OTHER REQS ARE MET
        if 'OPEN' in req_values:
            pass


        return req_values

    # > have it so that each requirement is processed in order, and it REMOVES the input items which met the req
    # (this makes it easy for the OPEN req parsing to work)

    # > this returns all req values -> maybe add option to only do keywords - but don't do seperate function
    # otherwise _get_input_req_value still needs to be outside -> in which case it needs to ALWAYS return the matched words as values, 
    # and keep any other overidden value as an entire seperate thing.
    # then, this would use a while loop, rather than list comprehension or for loop, and the input list will be modified as it goes


    def generate_command_action(self, input_req_values:tuple):
        """generates and returns a command action from the provided input-requirement-values"""
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
            
        


class CommandAction:
    def __init__(self):
        pass


#-------------------------------
# Core helper classes

class CommandActionRunner:
    def __init__(self, UI:TextAudioUI):
        pass


class VoiceInputCommandProcessor:
    def __init__(self, UI:TextAudioUI, commands:list[Command], wakewords:str):
        self._UI = UI
        self._transcriber = stt.Transcriber()
        self._wake_timer = time_tools.Timer(5, self._wake_timeout)      # keeps track of wakfulness in real time
        
        self._wakewords = wakewords
        self._all_command_keywords = self._generate_command_keywords(commands)  # all command keywords - used for transcriber vocabulary
        
        self._current_input = []                                        # all of the current input for a single cycle
        self._current_command = None                                    # the name of command whose keywords have been matched

    #---------

    def _add_to_current_input(self, input_audio:bytes):
        self._current_input.append(
            {
                'audio':    input_audio,
                'text1':    None,
                'text2':    None
            }
        )

    def reset_command_input(self):
        """resets current input cycle"""
        self._current_input.clear()
        self._current_command = None
    
    #---------
    # methods for wake word functionality

    def _wake_start(self):
        self._wake_timer.start()
        # vvv should eventually be a visual colour indication of wakefullness -> something lights up when awake, and stops when timer runs out
        self._UI.nl_print('\n\n---waking!---')
    
    def wake_stop(self):
        self._wake_timer.stop()
        # AGAIN, replace with visual colour change or something

    def _wake_timeout(self):
        self.reset_command_input()
        # AGAIN, replace with visual colour change or something
        self._UI.nl_print('wake timer ran out!')

    def validiate_input(self, input_audio:bytes, wakewords:str) -> bool:
        """Check if input audio contains wakeword(s) or is within wake timeout.
        Wakewords must be a single word or multiple seperated by whitespace"""
        if self._transcriber.transcribe(input_audio, wakewords):
            self.reset_command_input()
            self._wake_start()
        elif self._wake_timer.is_active():
            pass
        else:
            return False
        return True
    
    #---------
    # methods for input transcription

    @staticmethod
    def _generate_command_keywords(commands:list[Command]) -> str:
        """generate `all_command_keywords` str from the combination of every command's input keyword vocabulary"""
        # combine each command's input_keyword_vocab set into a tuple with comprehension
        # create a new set of every item within those keyword sets by unpacking the tuple and passing it to set().union()
        # and then join that set into a single string of words
        return ' '.join(set().union(*(command.keyword_input_vocab for command in commands)))

    def _transcribe_current_input_audio(self):
        """transcribe each phrase in current_input depending on stage in input cycle
        (either looking for all commands by keyword, or looking at a single command reqs)"""
        for phrase in self._current_input:
            # if the phrase has not yet been transcribed (within the corresponding text feild),
            # and no command has been found yet, then transcribe it using all command keywords as vocabulary
            if not self._current_command and not phrase['text1']:
                text = self._transcriber.transcribe(phrase['audio'], self._all_command_keywords)
                phrase['text1'] = text if text else '_'
            # but if a command has been found, then transcribe it using the current_command's input requirements as vocabulary
            elif self._current_command and not phrase['text2']:
                if 'OPEN' in current_command:
                    text = self._transcriber.transcribe(phrase['audio'])
                else:
                    text = self._transcriber.transcribe(phrase['audio'], self._current_command.all_input_vocab)
                phrase['text2'] = text if text else '_'

    #---------
    # general accessible functions

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
                    if command.get_keyword_req_value(self.get_current_input_text(), command):
                        self._current_command = command
                        continue
            else:
                input_req_values = self._current_command.get_all_req_values(self.get_current_input_text())
                if all(input_req_values):
                    # if all input requirements are met, generate an action and return it
                    action = self._current_command.generate_command_action(input_req_values)
                    return action
            break


#-------------------------------
# App Core class

# aka Input-to-Command Executer
class AppCore:
    def __init__(self, commands:list[Command]):
        self._active = False
        self._commands = commands                       # stores all command objects

        self._UI = TextAudioUI()
        self._vox_proc = VoiceInputCommandProcessor(self._UI, self._commands, 'computer')

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
        return self._UI.get_voice_audio()               # this is blocking

    def _get_command_from_input(self, user_input):
        if isinstance(user_input, str):
            # print out input
            for command in self._commands:
                action = get_command_action_from_input(user_input, command)
                if action:
                    break
        elif isinstance(user_input, bytes):
            valid = self._vox_proc.validiate_input()
            if valid:
                action = self._vox_proc.add_input_audio_get_action(user_input, self._commands)
                # print out input
                if action:
                    self._vox_proc.wake_stop()                 # turn off wake timer, so no new audio phrase input can be accepted again
                    self._vox_proc.reset_command_input()       # reset input cycle values
        # elif is audio bytes BUT got through button-press-audio-input instead of phrase_detector:
            # do same as above, but don't validate

        return action

    
    def _do_command_action(self, action):
        pass
    # [3] if get an action back from command, run the command action (in seperate thread)

    def _main_loop(self):
        while self._active:
            user_input = self._get_input()
            com_action = self._get_command_from_input(user_input)
            if com_action:
                # self._UI.nl_print(f'now doing {com_action.name}')
                self._do_command_action(com_action)

    #---------

    def run(self):
        self._UI.nl_print('loading...')
        self._active = True
        self._UI.start()                        # start UI
        self._UI.nl_print('starting!')
        self._main_loop()
