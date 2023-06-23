from external_scripts import number_tools, time_tools, word_tools
from app_components import Command, AppCore

#-------------------------------
# command objects

commands = [
    Command(
        name=   'Shutdown',
        input=  (
                    ['app', 'shutdown'],
                ),
        func=   'SHUTDOWN',
        output= 'shutting down'
    ),
    Command(
        name=   'Get Time',
        input=  (
                    'time',
                ),
        func=   time_tools.get_current_local_time_str,
        output= "the current time is [FUNC]"
    ),
    Command(
        name=   'Get Date',
        input=  (
                    'date',
                ),
        func=   time_tools.get_current_local_date_str,
        output= "today's date is [FUNC]"
    ),
]

#---
# commands to add later

"""
    Command(
        name=       'Set Alarm',
        input=      (
                        'alarm',
                        'TIME',
                    ),
        func=       lambda a : a + 10,
        args=       ('[1]',),
        output=     'alarm set for [1]'  
    )
"""

#-------------------------------
# main script

if __name__ == "__main__":
    app = AppCore(commands)
    app.run()
    print('goodbye!')