from tkinter import *
from tkinter import filedialog
import plotly.express as px
import pandas as pd


def browseFiles():
    global filename
    filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("csv files",
                                                        "*.csv*"),
                                                       ("all files",
                                                        "*.*")))
    
    selected_file(filename)
    return filename

def selected_file(filename):
    print(filename)
      
                                                                                                  
window = Tk()
  
window.title('LMT cvs to graph')
  
window.geometry("300x300")

window.config(background = "white")
  
label_file_explorer = Label(window,
                            text = "Trend graph",
                            width = 33, height = 4,
                            fg = "black",
                            font=20)
  
button_explore = Button(window,
                        text = "Browse Files",
                        command = browseFiles,
                        height=2,
                        width=20)
  
button_exit = Button(window,
                     text = "Exit",
                     command = exit,
                     height=2,
                     width=20)
  
label_file_explorer.grid(column = 0, row = 1)
  
button_explore.grid(column = 0, row = 2)
  
button_exit.grid(column = 0,row = 3)
  

window.mainloop()

print(filename)
