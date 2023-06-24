from datetime import datetime, timezone
from time import time
from threading import Thread, Event

#-------------------------------
# time string formats

STRF_YR__SEC_CMPCT = '%Y%m%d%H%M%S'
STRF_YR__SEC_H24 = "%Y-%m-%d %H:%M:%S"
STRF_YR__SEC_H12 = "%Y-%m-%d %I:%M:%S %p"
STRF_YR__MIN_H24 = "%Y-%m-%d %H:%M"
STRF_YR__MIN_H12 = "%Y-%m-%d %I:%M %p"
STRF_HR_MIN_H24 = '%H:%M'
STRF_HR_MIN_H12 = '%I:%M %p'
STRF_YR_MNT_DY = '%Y %B %d'
STRF_WDY_MNT_DY = '%A, %B %d'

#-------------------------------
# datetime functions

def get_current_utc_datetime() -> datetime:
    """get a datetime object representing the current time in the UTC time zone"""
    return datetime.now(timezone.utc)

def get_current_local_datetime() -> datetime:
    """get a datetime object representing the current time in the local time zone"""
    return datetime.now().astimezone()

def convert_datetime_to_local(dt: datetime) -> datetime:
    """convert any datetime object to match the corresponding local datetime"""
    return dt.astimezone()

def convert_datetime_to_utc(dt: datetime) -> datetime:
    """convert any datetime object to match the corresponding UTC datetime"""
    return dt.astimezone(tz=timezone.utc)

#def get_new_datetime() -> datetime:
#    now = get_current_local_datetime()
#    now.replace()

#-------------------------------
# datetime-string functions

def format_datetime_to_string(dt:datetime, frmt:str) -> str:
    return datetime.strftime(dt, frmt)

def get_current_local_time_str() -> str:
    """returns a string containing the current local time in 12 hour format"""
    return datetime.strftime(datetime.now(), STRF_HR_MIN_H12)

def get_current_local_date_str() -> str:
    """returns a string containing the current local date"""
    return datetime.strftime(datetime.now(), STRF_WDY_MNT_DY)

#-------------------------------
# timer class

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
            if time() >= self._target and self.is_active():
                self._func(*self._args)
                self.stop()

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
