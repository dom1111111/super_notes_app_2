import tkinter
from tkinter import ttk

class tk_GUI_tools:
    def __init__(self):
        pass

    #---------
    # functions for setting up window geometry

    def center_tk_window_geometry(self, window_object:tkinter.Tk, width:int, height:int):
        # get dimensions of computer screen
        screen_width = window_object.winfo_screenwidth()
        screen_height = window_object.winfo_screenheight()
        # make sure the window can't be bigger than 90% of the screen
        if width > screen_width * 0.90:
            width = int(screen_width * 0.90)
        if height > screen_height * 0.90:
            height = int(screen_height * 0.90)
        # find center coordinates of screen, and top-left coordinates of window relative to center
        center_x = int(screen_width/2 - width/2)
        center_y = int(screen_height/2 - height/2)
        # set geometry
        window_object.geometry(f'{width}x{height}+{center_x}+{center_y}')   # argument is the starting size of the window in pixels (width, height) and position of top-left corner on the computer screen (x, y) 

    def set_tk_window_geometry_sensibly(self, window_object:tkinter.Tk, percentage:int):
        """
        This will create a window which is horizontally centered, and just above the vertical center, on the screen
        - `percentage` is the percentage of the screen's dimensions that the window's dimensions will take up
            - This is limited to 90%
        """
        # set percentage limit to 90
        if percentage > 90:
            percentage = 90
        # get dimensions of computer screen
        screen_width = window_object.winfo_screenwidth()
        screen_height = window_object.winfo_screenheight()
        width = int(screen_width * percentage/100)
        height = int(screen_height * percentage/100)
        # find center coordinates of screen, and top-left coordinates of window relative to center
        center_x = int(screen_width/2 - width/2)
        center_y = int((screen_height/5 * 2) - height/2)    # makes sure window y-position is near between top and middle of screen
        if center_y < 0:                                    # makes sure that window won't go off screen
            center_y = 0
        # set window height, width, and x/y coordinates of its top-left corner - all in pixels
        window_object.geometry(f'{width}x{height}+{center_x}+{center_y}')
        # set minimum height and width of window to be 25% of screen's height and width
        window_object.minsize(int(screen_width*0.25), int(screen_height*0.25))

#---------

#class GUI():
    # def build_GUI(self)

#---------
# Build GUI

tk_tools = tk_GUI_tools()

# 1. create main window
window = tkinter.Tk()
#window.state('zoomed')
window.title("edomode")
tk_tools.set_tk_window_geometry_sensibly(window, 60)

# 2. create/adjust widget styles


# 3. create widgets
#main_view_frame = ttk.Frame(window, padding=12)
main_view = tkinter.Text(window, height=40, bg='dark grey', fg='blue', padx=4, pady=4, state='disabled')
log_box = tkinter.Text(window, height=10, bg='black', fg='white', padx=4, pady=4, state='disabled')


# 4. Place widgets using `grid` geometry manager
main_view.grid(row=0, column=0, sticky=('n','s','e','w'))
log_box.grid(row=1, column=0, sticky=('n','s','e','w'))


# 5. So you need to do column and row configure to both the window and any frames if you want things to be resizeable
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=4)
window.rowconfigure(1, weight=1)
#   > NOTICE the weight between rows in the same ratio as the items within them! (4:1, and 40:10 height for Text widgets!)

#---------
# Functions to affect GUI

def append_to_log(message:str):
    log_box.config(state='normal')          # state must be normal in order for anything to happen to the log
    log_box.insert('end', message + '\n\n') # 'end' is the index for the end of the text, and the other string is the text to insert
    log_box.see('end')                      # makes sure the view is always at the end index (it scrolls to the bottom: the newest message)
    log_box.config(state='disabled')        # then disable the text box, so that not editing can occur (read-only)

def append_to_mainview(message:str):
    main_view.config(state='normal')
    main_view.insert('end', message + '\n\n')
    main_view.see('end')
    main_view.config(state='disabled')

def clear_mainview():
    main_view.config(state='normal')
    main_view.delete('1.0', 'end')          # the two arguments are the start and end index
    main_view.config(state='disabled')

def run_GUI():
    window.mainloop()

def stop_GUI():
    window.quit()

def terminate_GUI():
    # CAN ONLY CALL THIS ONCE
    window.destroy()
