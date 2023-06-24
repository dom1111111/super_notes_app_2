"""
contains all classes needed to run the app
"""
from time import sleep
from datetime import datetime
from threading import Lock, Thread, Event
from queue import Queue
from functools import wraps
from typing import Callable
from external_scripts import stt, tts, play_rec_audio, GUI_tk, number_tools, time_tools, word_tools

#-------------------------------
# UI classes

class _SharedResourceWrapper:
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
    _vox_in_wrap = _SharedResourceWrapper()
    _vox_out_wrap = _SharedResourceWrapper()
    _audio_out_wrap = _SharedResourceWrapper()
    _terminal_wrap = _SharedResourceWrapper()
    _TUI_wrap = _SharedResourceWrapper()

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
        If '[FUNC]' is within the string, then it will be replaced with the return value of func attribute.
        Like with args, if an input requirement index (ex: [1]) is within the string, then it will replaced with its value
    """
    
    def __init__(self, name:str, input:tuple, func:Callable|str, args:tuple=(), output:str=''):
        self.name = name
        self.input = tuple(self._get_req_data(r) for r in input)
        self.func = func
        self.args = args
        self.output = output

        self.keyword_input_vocab, self.all_input_vocab = self._get_input_req_words(input)

    #------
    # methods for getting/converting input-requirement data

    @staticmethod
    def _get_req_data(req:str|tuple|list) -> tuple:
        """convert an input requirement to a three-item-tuple (type, content, value)"""
        
        def process_multi_req(req:list):
            val = None
            for i, sub_r in enumerate(req):                             # check through the multi-item requirement,
                if isinstance(sub_r, set):                              # and if it contains a set,
                    val = req.pop(i)[0]                                 # remove the set and isolate the value within it (with [0] index)
                    break                                               # break for loop once set is found (there should only ever be one set! any other's will be ignored)
            # further convert any nested requirements, then return these as overall content
            cont = tuple(Command._get_req_data(sub_r) for sub_r in req if not isinstance(sub_r, set))
            return cont, val
        
        # determine the requirement type by its value or data-type
        if req == 'NUMBER' or req == 'TIME' or req == 'OPEN':           # single string, special value type
            return (req, None, None)
        elif isinstance(req, tuple):                                    # tuples represent ANY type
            cont, val = process_multi_req(list(req))
            return ('ANY', cont, val)
        elif isinstance(req, list):                                     # lists represent ALL type
            cont, val = process_multi_req(req)
            return ('ALL', cont, val)
        else:                                                           # single string type
            return ('STR', req, None)

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

    #------
    # methods for checking user input against input requirements

    @staticmethod
    # this is used solely for get_req_value methods below
    def _get_input_req_value(req_type:str, req_content:str|tuple|list, u_in_items:list[str|int|float]):
        """Get the value of a single input requirement based its type and content, if it is matched in list of user input items"""

        if req_type == 'STR':
            return req_content if req_content in u_in_items else None
        elif req_type == 'NUMBER':
            nums = tuple(x for x in u_in_items if (isinstance(x, int) or isinstance(x, float)))
            return nums[0] if nums else None        # only return the first instance of a number
        #elif req_type == 'TIME':
        #    times = tuple(x for x in u_in_items if isinstance(x, ,,,))
        #    return times[0] if times else None     # only return the first instance of a time
        elif req_type == 'OPEN':
            return 'OPEN'                           # this will be processed outside of this method, so just return 'OPEN' as value
        elif req_type == 'ANY':
            for sub_req in req_content:
                sub_val = Command._get_input_req_value(sub_req[0], sub_req[1], u_in_items)  # sub_req[0] and sub_req[1] is type and content respectively
                if sub_val:
                    return sub_val                  # return the first sub requirement which is met
        elif req_type == 'ALL':
            sub_vals = tuple(Command._get_input_req_value(sub_req[0], sub_req[1], u_in_items) for sub_req in req_content)
            return sub_vals if all(sub_vals) else None

    def get_keyword_req_value(self, user_input:str) -> tuple:
        """returns a tuple of values for command's keyword input requirement, based on user input"""
        user_input_items = word_tools.get_words_only(user_input)            # get a list with all words or numbers in user input
        keyword_req = self.input[0]                                         # keyword req is first item (input[0])
        return self._get_input_req_value(keyword_req[0], keyword_req[1], user_input_items)   # [0] is req type, [1] is content

    def get_all_req_values(self, user_input:str) -> list:
        """returns a tuple of values for all command's input requirements, based on user input"""
        user_input_items = word_tools.get_words_only(user_input)            # get a list with all words, numbers, times in user input
        req_values = []

        for req in self.input:
            value = self._get_input_req_value(req[0], req[1], user_input_items) # get value of req based on user input items
            # `sub_req[0]` and `sub_req[1]` is type and content respectively
            if value:                                                       # if a value is returned (a user input item which met the requirement),
                if req[0] in ('STR', 'NUMBER', 'TIME', 'ANY'):              # and it's any type except 'ALL' or 'OPEN', then remove the matched item from user_input_items
                    user_input_items.remove(value)
                elif req[0] == 'ALL':                                       # otherwise if type is `ALL` (several items must've been matched), 
                    for sub_val in value:                                   # then remove each item from user_input_items
                        user_input_items.remove(sub_val)

                value = req[2] if req[2] else value                         # if a value (req[2]) was manually set in the requirement, then use that value instead

            req_values.append(value)                                        # add value to req_values (regardless if it was a match or not)

        # if there is 'OPEN' in req_values (an OPEN requirement) and all other values are True (all other reqs have been met),
        # then join all of the remaining items in user input and set this as the value for the OPEN requirement, 
        # excluding any conjunctions or uneeded words
        if 'OPEN' in req_values and all(req_values):
            pass
            # must keep order! -> need to only look at words happening 

        return req_values


#-------------------------------
# Core helper classes

class _VoiceInputCommandProcessor:
    def __init__(self, UI:TextAudioUI, commands:list[Command], wakewords:str):
        self._UI = UI
        self._transcriber = stt.Transcriber()
        self._wake_timer = time_tools.Timer(5, self._wake_stop)         # keeps track of wakfulness in real time
        
        self._wakewords = wakewords
        self.commands = commands
        self._all_command_keywords = self._generate_command_keywords()  # all command keywords - used for transcriber vocabulary
        
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

    def _reset_command_input(self):
        """resets current input cycle"""
        self._current_input.clear()
        self._current_command = None
    
    #---------
    # methods for wake word functionality

    def _wake_start(self):
        self._wake_timer.start()
        # vvv should eventually be a visual colour indication of wakefullness -> something lights up when awake, and stops when timer runs out
        self._UI.nl_print('\n\n---waking!---')
    
    def _wake_stop(self):
        self._wake_timer.stop()
        self._reset_command_input()
        # AGAIN, replace with visual colour change or something
        self._UI.nl_print('wake timer stopped!')

    def validiate_input(self, input_audio:bytes) -> bool:
        """Check if input audio contains wakeword(s) or is within wake timeout.
        Wakewords must be a single word or multiple seperated by whitespace"""
        if self._transcriber.transcribe(input_audio, self._wakewords):
            self._reset_command_input()
            self._wake_start()
        elif self._wake_timer.is_active():
            self._wake_start()
        else:
            return False
        return True
    
    #---------
    # methods for input transcription

    def _generate_command_keywords(self) -> str:
        """generate `all_command_keywords` str from the combination of every command's input keyword vocabulary"""
        return ' '.join(set(' '.join(command.keyword_input_vocab for command in self.commands).split()))
        # ^ combine each command's input_keyword_vocab string with comprehension, and then join that into a single string
        # split that string into individual words, and convert it into a set to remove duplicates
        # and then join that set into a single string of words

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
                if 'OPEN' in (req[0] for req in self._current_command.input):   # this checks if current command contains any input requirements with the type ([0]) 'OPEN'
                    text = self._transcriber.transcribe(phrase['audio'])
                else:
                    text = self._transcriber.transcribe(phrase['audio'], self._current_command.all_input_vocab)
                phrase['text2'] = text if text else '_'

    #---------
    # general accessible functions

    def get_current_input_text(self) -> str:
        t_key = 'text2' if self._current_command else 'text1'
        return ' '.join(phrase[t_key] + ',' for phrase in self._current_input if phrase[t_key])

    
    def check_input_get_command_and_values(self, input_audio:bytes) -> tuple[Command, tuple]:
        """Pass in audio input and check if it (and previously passed in input within the same wake timeout) 
        matches all of the command's input requirements. If it does, will return a command and its input requirement values.
        """
        print('checking for commands')
        self._add_to_current_input(input_audio)         # add input to current audio
        self._transcribe_current_input_audio()          # trasncribe ALL current audio (either with just keywords, or with current_command vocab)
        input_text = self.get_current_input_text()
        
        req_vals = None

        def check_all_reqs():
            print('is now current command')
            input_req_values = self._current_command.get_all_req_values(input_text)
            if all(input_req_values):
                self._wake_stop()                       # turn off wake timer, so no new audio phrase input can be accepted again without using the wakeword + reset input cycle values
                return input_req_values

        if not self._current_command:                   # first check if current_input text matches a command's keyword input requirements
            print('is not yet current command')
            for command in self.commands:
                if command.get_keyword_req_value(input_text):
                    self._current_command = command     # set current_command to the command whose keyword requirement was matched
                    req_vals = check_all_reqs()         # then check current_command's requirements
                    break
        else:                                           # if a command was matched, check if current_input matches all of the current command's input requirements
            req_vals = check_all_reqs()

        print('>>>>', self._current_command, req_vals)
        return self._current_command, req_vals


#-------------------------------
# App Core class

# aka Input-to-Command Executer
class AppCore:
    """
    Instatiate this class, passing in a list of `Command` objects, and call the `run()` method to run the app
    """
    def __init__(self, commands:list[Command]):
        self._active = False
        self._commands = commands 
        self._prep_commands()

        self._UI = TextAudioUI()
        self._vox_proc = _VoiceInputCommandProcessor(self._UI, self._commands, 'computer')

    #---------
    # methods for internal command actions

    def _shutdown(self):
        self._UI.nl_print('shutting down...')
        self._active = False
        self._UI.stop()
        #self._UI.end_GUI()

    #---
    # method to prepare commands as needed

    def _prep_commands(self):
        """changes any refference strings in command funcs to the methods they represent"""
        str_func_map = {
            'SHUTDOWN': self._shutdown,
        }

        for command in self._commands:
            # if the command's function is a string, then match it to a corresponding internal method
            if isinstance(command.func, str):
                command.func = str_func_map.get(command.func)

    #---------
    # main loop helper methods

#NOTE >>> THIS CURRENT WON'T WORK IF NUMBERS ARE TYPED, etc. - must be adjusted to handle pure text input, not voice transcription text
    def _get_command_from_text_input(self, user_input:str) -> tuple[Command, tuple]:
        """return a command and its input requirement values if user_input matches all of a command's input requirements"""
        for command in self._commands:
            input_req_values = command.get_all_req_values(user_input)
            if all(input_req_values):
                return command, input_req_values
        return None, None
        
    def _get_command_from_audio_input(self, user_input:bytes) -> tuple[Command, tuple]:
        """return a command and its input requirement values if user_input matches all of a command's input requirements"""
        if self._vox_proc.validiate_input(user_input):          # first check if input is valid (contains wakeword, or is within current wake time)
            return self._vox_proc.check_input_get_command_and_values(user_input)
        return None, None

    def _generate_command_action(self, command:Command, input_req_values:tuple):
        """generates and returns a command action from the provided input-requirement-values"""
        
        def convert_arg_ref_to_val(x):
            """convert any string representing an index of one of the input requirement values into the value itself.
            should always look like: '[#]', where '#' is the index number"""
            try:
                assert x.startswith('[') and x.endswith(']')        # make sure that the string starts and ends with sqaure brackets
                return input_req_values[int(x[1:-1])]               # get to the string inbetween the sqaure brackets and convert it to an integer, then use that to index input_req_values for the corresponding value           
            except:
                return x

        def convert_mes_ref_to_val(mes:str, func_result) -> str:
            """convert any reffernces in the output string into the actual req values"""
            mes = mes.replace('[FUNC]', str(func_result))           # first convert any function result reffernces ('[FUNC]') to the actual function result
            while True:                                             # then convert any input_req_value refferences ('[n]') into actual values
                try:
                    ia = mes.index('[')                             # find index of first left sqaure bracket
                    ib = mes.index(']')                             # find index of first right sqaure bracket
                    mes = mes.replace(mes[ia:ib+1], input_req_values[int(mes[ia+1:ib])])
                    # ^ replace the index refference substring (both sqaure brackets and everything inbetween),
                    # with the corresponding value at the input_req_values index (the number in between the sqaure brackets)
                except:
                    break
            return mes
            
        # generate the action function
        def action():
            result = command.func(*(convert_arg_ref_to_val(arg) for arg in command.args)) if command.args else command.func()
            if command.output:
                self._UI.nl_print(convert_mes_ref_to_val(command.output, result))

        return action
    
    def _do_command_action(self, action:Callable):
        """run the command action in a new thread"""
        Thread(target=action, daemon=True).start()

    #---------
    # main loop

    def _main_loop(self):
        while self._active:
            # (1) get input
            user_input = self._UI.get_voice_audio()     # this is blocking
            # (2) check for a matching command from input (and display input)
            if isinstance(user_input, str):
                command, input_req_values = self._get_command_from_text_input(user_input)
                input_text = user_input
            elif isinstance(user_input, bytes):
                command, input_req_values = self._get_command_from_audio_input(user_input)
                print('command:', command)
                print('inp_req_vals:', input_req_values)
                input_text = self._vox_proc.get_current_input_text()
            if input_text:                              # print input text if there is some 
                self._UI.nl_print(f'🗣  "{input_text}" --- req-values: "{input_req_values}"')
            # (3) if command is matched, generate an action from the command input requirement values
            if input_req_values:
                self._UI.nl_print('command found!')
                action = self._generate_command_action(command, input_req_values)
            # (4) execute command action
                self._UI.nl_print(f'now executing "{command.name}" command action')
                self._do_command_action(action)

    #---------

    def run(self):
        self._UI.nl_print('loading...')
        self._active = True
        self._UI.start()                        # start UI
        self._UI.nl_print('started!')
        self._main_loop()
