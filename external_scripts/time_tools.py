from datetime import datetime, timedelta
from threading import Thread, Timer
from time import sleep
#from play_rec_audio import PlayAudio

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

#class 
