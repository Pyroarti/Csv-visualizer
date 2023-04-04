from tkinter import *
from tkinter import filedialog
import plotly.express as px
import pandas as pd
import tkinter as tk
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import threading
import webbrowser
import time
import customtkinter
import os
from PIL import Image
import moviepy.editor as mp
import subprocess
from os import startfile

customtkinter.set_appearance_mode("dark") 
customtkinter.set_default_color_theme("blue")

EXTENSION = "csv"

checked = []

filenames = []


def browseFiles():
    global filename
    filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("csv files",
                                                        "*.csv*"),
                                                       ("all files",
                                                        "*.*")))
    

    

    filenames.append(filename)
    after_file_selected()
    
    return filenames


def after_file_selected():
    global frame
    global header
    dfs = []

    def custom_date_parser(date_str):
        return pd.to_datetime(date_str, format='%m/%d/%Y %I:%M:%S %p')
    
    for filename in filenames:
         df = pd.read_csv(filename, parse_dates=['Time'], date_parser=custom_date_parser)
         dfs.append(df)
    frame = pd.concat(dfs, axis=0, ignore_index=True)
    

    frame = frame.dropna()
    print(frame)
    frame['Time'] = pd.to_datetime(frame['Time'])


    header = pd.read_csv(filename, index_col=0, nrows=0).columns.tolist()
    header = header[1:]
    
    app.create_dynamic_checkboxes(header)
    return frame, header


def create_dash_app(header, frame, checked):
    fig = px.line(frame, x="Time", y=header)

    app = dash.Dash(__name__)
    time.sleep(1)
    webbrowser.open_new('http://127.0.0.1:8050/')


    app.layout = html.Div([
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed=frame['Time'].min(),
            max_date_allowed=frame['Time'].max(),
            initial_visible_month=frame['Time'].min(),
            start_date=frame['Time'].min().date(),
            end_date=frame['Time'].max().date()
        ),
        html.Div(id='hour-range-slider-output'),
        dcc.RangeSlider(
            id='hour-range-slider',
            min=0,
            max=23,
            step=1,
            value=[0, 23],
            marks={i: f'{i}:00' for i in range(0, 24)}
        ),
        dcc.Graph(id='line-graph')
    ])


    @app.callback(
    Output('hour-range-slider-output', 'children'),
    [Input('hour-range-slider', 'value')]
    )
    def update_output(value):
        return f'Selected hour range: {value[0]}:00 - {value[1]}:00'


    @app.callback(
    Output('line-graph', 'figure'),
    [Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('hour-range-slider', 'value')]
    )   

    
    def update_graph(start_date, end_date, hour_range):
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        start_time = start_date.replace(hour=hour_range[0])
        end_time = end_date.replace(hour=hour_range[1])

        filtered_data = frame[(frame['Time'] >= start_time) & (frame['Time'] <= end_time)]
        fig = px.line(filtered_data, x='Time', y=header)

        selected_columns = [header[i] for i in checked]
        fig = px.line(filtered_data, x='Time', y=selected_columns)

        return fig

    
    app.run_server(debug=False)


def show_graph():
    dash_thread = threading.Thread(target=create_dash_app, args=(header, frame, checked))
    print(checked)
    dash_thread.start()


class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("700x300")
        self.resizable(False, False)
        self.title("LMT csv visualizer")
        with open("help_text.txt", "r") as f:
            help_text = f.read()

        self.label = customtkinter.CTkLabel(self, text=help_text,justify="left")
        self.label.pack(padx=20, pady=20)

        self.button_show_graph = customtkinter.CTkButton(master=self, command=self.play_video, text="See video tutorial")
        self.button_show_graph.pack(pady=10, padx=10)

    def play_video(self):
        # Load the video file using moviepy
        startfile("Help.mp4")



class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.checkbox_vars = []
        self.toplevel_window = None

        self.geometry("400x780")
        self.title("LMT csv visualizer")

        self.resizable(False, False)


        current_path = os.path.dirname(os.path.realpath(__file__))
        self.bg_image = customtkinter.CTkImage(Image.open(current_path + "\\bg.jpg"),
                                               size=(400, 780))
        self.bg_image_label = customtkinter.CTkLabel(self, image=self.bg_image)
        self.bg_image_label.place(x=0, y=0, relwidth=1, relheight=1)


        self.frame_1 = customtkinter.CTkFrame(master=self, bg_color="transparent")
        self.frame_1.place(relx=0.5, rely=0.5, anchor="center")

        self.frame_1 = customtkinter.CTkFrame(master=self)
        self.frame_1.pack(pady=20, padx=40, fill="both", expand=True)


        Lable1 = customtkinter.CTkLabel(master=self.frame_1, justify=customtkinter.LEFT, text="Visualize csv data",font=customtkinter.CTkFont(size=20, weight="bold"),bg_color="transparent")
        Lable1.pack(pady=10, padx=10)

        button_explore = customtkinter.CTkButton(master=self.frame_1, command=browseFiles, text="Browse files")
        button_explore.pack(pady=10, padx=10)

        button_show_graph = customtkinter.CTkButton(master=self.frame_1, command=show_graph, text="Show graph")
        button_show_graph.pack(pady=10, padx=10)

        button_help = customtkinter.CTkButton(master=self.frame_1, command=self.open_toplevel, text="How to use")
        button_help.pack(pady=10, padx=10)

        button_exit = customtkinter.CTkButton(master=self.frame_1, command=exit, text="Exit")
        button_exit.pack(pady=10, padx=10)

        


    def create_dynamic_checkboxes(self, header):
        self.scrollable_frame = customtkinter.CTkScrollableFrame(master=self.frame_1, height=200)
        self.scrollable_frame.pack(fill="both", expand=True)
 
        Lable2 = customtkinter.CTkLabel(master=self.scrollable_frame, justify=customtkinter.LEFT, text="Select what component(s) to visualize",font=customtkinter.CTkFont(size=14, weight="bold"))
        Lable2.pack(pady=10, padx=10)

        for idx, name in enumerate(header):
            checkbox_var = IntVar()
            checkbox_1 = customtkinter.CTkCheckBox(master=self.scrollable_frame, text=name, variable=checkbox_var, command=lambda index=idx: self.on_checkbox_change(index))

            checkbox_1.pack(pady=10, padx=10)
            self.checkbox_vars.append(checkbox_var)

        scrollbar = customtkinter.CTkScrollbar(master=self.scrollable_frame, orient=VERTICAL, command=self.scrollable_frame.yview)
        self.scrollable_frame.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y, master=self.scrollable_frame)

    def on_checkbox_change(self,index):
    
        if self.checkbox_vars[index].get() == 1:
            checked.append(index)
        else:
            checked.remove(index)


    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)  
        else:
            self.toplevel_window.focus() 

        self.toplevel_window.lift()



if __name__ == "__main__":
    app = App()
    app.mainloop()



