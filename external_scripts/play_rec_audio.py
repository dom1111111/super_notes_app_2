"""
Two classes that uses the Pyaduio module to start, pause, and stop audio playing and recording!

* Instantiate `PlayAudio` for playing audio, 
* `RecAudio` for recording audio
"""

import pyaudio
import wave
from time import sleep

pa = pyaudio.PyAudio()                      # instantiate PyAudio

class _BaseAudio:
    """
    Methods:
    * `get_state()` - return whether or not stream is active
    * `pause_resume()` - pause and resume audio playing
    * `stop()` - ends the audio playing and closes the stream
    """

    def _stream_check_wrapper(func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'stream'):     # checks if 'stream' exists (it won't exist if nothing was played/recorded yet)
                func(self, *args, **kwargs)
        return wrapper

    def get_state(self):
        """
        Returns current state of the stream:
        * `"OA"`: stream is open and active
        * `"OP"`: stream is open and paused
        * `"OI"`: stream is open and inactive
        * `"C"`: stream is closed
        """
        if hasattr(self, 'stream'):
            if self.stream.is_active():
                return 'OA'
            elif self.stream.is_stopped():
                return 'OP'
            else:
                return 'OI'
        else:
            return "C"
    
    @_stream_check_wrapper
    def pause_resume(self):
        """
        If the stream is active, this will stop the stream (essentially pausing it). If it is stopped, it will start the stream again.
        """
        if self.stream.is_active():
            self.stream.stop_stream()       # pauses the stream
        elif self.stream.is_stopped():
            self.stream.start_stream()      # resumes the stream
    
    @_stream_check_wrapper
    def stop(self):
        """
        Stop audio processing and close the stream
        """
        self.stream.close()
        del self.stream                     # this is neccessary to avoid errors!

class PlayAudio(_BaseAudio):
    """
    * `play(audio_file_path)` - play audio in a seperate thread
    """

    def play(self, audio_file_path:str, wait:bool=False):
        """
        Play audio in a seperate thread (non-blocking).
        If `wait` is set to true, then this WILL block for the duration of the audio.
        """
        # if there is already an open stream, close it first
        if hasattr(self, 'stream'):
            self.stream.close()

        self.file = wave.open(audio_file_path, 'rb')

        # these are collected in case wait is True
        framerate = self.file.getframerate()
        n_frames = self.file.getnframes()

        def callback(in_data, frame_count, time_info, status):
            data = self.file.readframes(frame_count)
            return (data, pyaudio.paContinue)

        # open stream with PyAudio-instance's open()
        self.stream = pa.open(
            format = pa.get_format_from_width(self.file.getsampwidth()),
            channels = self.file.getnchannels(),
            rate = framerate,
            output = True,                  # 'Specifies whether this is an output stream. Defaults to False.'
            stream_callback = callback
            )

        self.stream.start_stream()
        
        # if `wait` is True, then sleep (block) for the duration of the audio
        if wait:
            audio_duration = n_frames/framerate
            sleep(audio_duration)
    
    # extends the parent class stop() method to also close the audio file
    def stop(self):
        super(PlayAudio, self).stop()
        self.file.close()

class RecAudio(_BaseAudio):
    """
    * `get_pars` - return a tuple of the current audio parameters
    * `set_pars` - set up the audio parameters
    * `reset_pars` - reset the audio parameters to their original values
    * `set_callback` - override the normal recording callback function
    * `reset_callback` - reset back to normal recording callback function
    * `record()` - start a recording in a sperate thread
    * `stop_and_return()` - ends the audio recording and returns the raw audio data
    * `write_to_file(audio, file_path)` - takes in audio data and writes it to a wave file accroding to the file path given
    """

    def __init__(self):
        self.CHUNK = 1024                   # https://dsp.stackexchange.com/questions/13728/what-are-chunks-when-recording-a-voice-signal
        self.FORMAT = pyaudio.paInt16       # https://people.csail.mit.edu/hubert/pyaudio/docs/#pasampleformat
        self.CHANNELS = 1
        self.RATE = 44100

        self.audio_frames = []              # a list to store the recorded audio data
        self._callback_func = None
    
    def get_pars(self) -> tuple:
        """
        Returns a tuple containing the current audio parameters:
        * number of samples per chunk/buffer aka 'chunk/buffer size'
        * number of channels
        * sample rate (number of samples in each second of audio)
        """
        return (self.CHUNK, self.CHANNELS, self.RATE)

    def set_pars(self, chunk_size:int, n_channels:int, rate:int):
        """
        Pass arguments to set the audio parameters:
        * `chunk_size` - number of samples per chunk
        * `n_channels` - number of channels
        * `rate` - number of samples captured per second
        """
        self.CHUNK = chunk_size
        self.CHANNELS = n_channels
        self.RATE = rate

    def reset_pars(self):
        """
        Resets audio paramters to original values:
        * `CHUNK` = 1024
        * `CHANNELS` = 1
        * `RATE` = 44100
        """
        self.set_pars(1024, 1, 44100)

    def set_callback(self, func):
        """
        Overrides the behaviour of the normal recording callback function and instead calls the procided `func` argument.
        
        The `func` argument given MUST be a function, and accept audio data bytes (pyaudio callback `in_data`) as its only argument
        """
        if callable(func):
            self._callback_func = func

    def reset_callback(self):
        """
        Reset recording callback function to standard functionality
        """
        self._callback_func = None
    
    def record(self):
        """
        Begin recording audio from default recording device

        Call `stop_and_return()` to stop recording and return the audio data (bytes)
        """
        # close the stream if one is already open
        if hasattr(self, 'stream'):
            self.stream.close()

        def callback(in_data, frame_count, time_info, status):
            # if a callback function was given (`set_callback()`), then call that,
            # otherwise just append audio data (in_data) to `audio_frames`
            if self._callback_func:
                self._callback_func(in_data)
            else:
                self.audio_frames.append(in_data)
            return (in_data, pyaudio.paContinue)

        self.stream = pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=callback
            )

    def stop_and_return(self) -> bytes:
        """
        Close the audio stream and return audio data
        """
        self.stop()
        if self.audio_frames:                                           # checks if stream is closed and audio frames is not empty
            audio_data = b''.join(self.audio_frames)                    # the b''.join is to join the bytes/chunks together
            self.audio_frames.clear()                                   # reset the frames list to be empty for the next audio
            return audio_data
    
    def write_to_file(self, audio_data:bytes, file_path:str):
        """
        Takes raw audio data (bytes) and writes it to a wav file
        """
        if audio_data and isinstance(audio_data, bytes):                # first check that audio data is not none and is a bytes type
            sample_width  = pa.get_sample_size(self.FORMAT)

            with wave.open(file_path, 'wb') as file:
                file.setnchannels(self.CHANNELS)
                file.setsampwidth(sample_width)
                file.setframerate(self.RATE)
                file.writeframes(audio_data)
                file.close()
        else:
            pass
            # raise?
