from datetime import datetime
from threading import Thread, Event
from time import time

#-------------------------------

TIME_STR_FRMT_1 = '%Y%m%d%H%M%S%f'
TIME_STR_FRMT_2 = '%I:%M %p'
DATE_STR_FRMT_1 = '%Y %B %d, %A'
DATE_STR_FRMT_2 = '%A, %B %d'

def validate_if_within_timeout(current_time:datetime, last_time:datetime, timeout:int):
    if (current_time - last_time).seconds <= timeout:
        return True

def get_current_time(cls):
    return datetime.now().strftime(TIME_STR_FRMT_2)

def get_current_date():
    return datetime.now().strftime(DATE_STR_FRMT_2)

class Timer:
    """
    Call a function after a specified timeout in seconds.

    This will start a new thread if the timer has not been started, 
    but if a timer is restarted while still active, 
    the previous thread will be kept alive and only the delay timeout will be reset.
    This way, a new thread is only spawned when needed.
    """
    def __init__(self, timeout:int, func, *args):
        self._timeout = timeout
        self._func = func
        self._args = args
        self._target = time()
        self._t = Event()
        self.stop()

    def _main_func(self):
        self._t.clear()
        while self.is_active():
            self._t.wait(self._target - time())
            if time() >= self._target:
                self._func(*self._args)
                self._t.set()
                break

    def start(self):
        "start the timer"
        self._target = time() + self._timeout
        if not self.is_active():
            Thread(target=self._main_func, daemon=True).start()
    
    def stop(self):
        "stop and reset the timer"
        self._t.set()

    def is_active(self):
        "return `True` if timer is active, and `False` is not"
        return not self._t.is_set()
