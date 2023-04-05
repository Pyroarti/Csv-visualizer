from tkinter import IntVar, filedialog, messagebox
import threading
import os
from os import startfile
import signal
import webbrowser
import time

import customtkinter
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from PIL import Image
from waitress import serve


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

HELP_TEXT_FILE = "help_text.txt"
HELP_VIDEO_FILE = "Help.mp4"
BACKGROUND_IMAGE = "bg.jpg"

components_checked = []

filenames = []

def browseFiles(app_instance):
    global filename
    initial_dir = os.getcwd()
    
    filename = filedialog.askopenfilename(initialdir = initial_dir,
                                          title = "Select a File",
                                          filetypes = (("csv files",
                                                        "*.csv*"),
                                                       ("all files",
                                                        "*.*")))


    if filename.endswith("csv"):
        filenames.append(filename)
        after_file_selected(app_instance)

    else:
        messagebox.showinfo("Invalid file type", "Please select a CSV file.")

    return filenames


def after_file_selected(app_instance):
    global data
    global components_name
    dfs = []

    def custom_date_parser(date_str):
        return pd.to_datetime(date_str, format='%m/%d/%Y %I:%M:%S %p')

    for filename in filenames:
        dataframe = pd.read_csv(filename, parse_dates=['Time'], date_parser=custom_date_parser)
        dfs.append(dataframe)
    data = pd.concat(dfs, axis=0, ignore_index=True)

    data = data.dropna()

    data['Time'] = pd.to_datetime(data['Time'])

    components_name = pd.read_csv(filename, index_col=0, nrows=0).columns.tolist()
    components_name = components_name[1:]

    app_instance.create_dynamic_checkboxes(components_name)
    return data, components_name


def create_dash_app(components_name, data, checked):
    fig = px.line(data, x="Time", y=components_name)

    app = dash.Dash(__name__)
    
    dcc.Graph(
    id='line-graph',
    style={'width': '100%', 'height': '150vh'}
    )


    app.layout = html.Div([
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed=data['Time'].min(),
            max_date_allowed=data['Time'].max(),
            initial_visible_month=data['Time'].min(),
            start_date=data['Time'].min().date(),
            end_date=data['Time'].max().date()
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
        dcc.Graph(id='line-graph',
        style={'width': '100%', 'height': '85vh'}
        )
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
        print(start_date)
        end_date = pd.to_datetime(end_date)

        start_time = start_date.replace(hour=hour_range[0])
        end_time = end_date.replace(hour=hour_range[1])

        filtered_data = data[(data['Time'] >= start_time) & (data['Time'] <= end_time)]
        fig = px.line(filtered_data, x='Time', y=components_name)

        selected_columns = [components_name[i] for i in checked]
        fig = px.line(filtered_data, x='Time', y=selected_columns)

        return fig

    #serve(app.server, host='127.0.0.1', port=8050)
    dash_thread = threading.Thread(target=serve, args=(app.server,), kwargs={'host': '127.0.0.1', 'port': 8050, '_quiet': True})
    dash_thread.daemon = True  # Set daemon to True to allow the app to exit when the main thread is closed
    dash_thread.start()
    webbrowser.open_new('http://127.0.0.1:8050/')


def show_graph():
    if components_checked:
        create_dash_app(components_name, data, components_checked)
    else:
        messagebox.showinfo("No component selected", "Please select atleast one component to plot.")


class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("700x300")
        self.resizable(False, False)
        self.title("LMT csv visualizer")

        with open(HELP_TEXT_FILE, "r",encoding="utf-8") as text_file:
            help_text = text_file.read()

        self.label = customtkinter.CTkLabel(self, text=help_text,justify="left")
        self.label.pack(padx=20, pady=20)

        self.button_show_graph = customtkinter.CTkButton(master=self, command=self.play_video, text="See video tutorial")
        self.button_show_graph.pack(pady=10, padx=10)


    def play_video(self):
        startfile(HELP_VIDEO_FILE)


class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.checkbox_vars = []
        self.toplevel_window = None

        self.geometry("400x500")
        self.title("LMT csv visualizer")

        self.resizable(False, False)


        self.bg_image = customtkinter.CTkImage(Image.open(BACKGROUND_IMAGE),
                                               size=(400, 780))
        self.bg_image_label = customtkinter.CTkLabel(self, image=self.bg_image)
        self.bg_image_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.frame_1 = customtkinter.CTkFrame(master=self, bg_color="transparent")
        self.frame_1.place(relx=0.5, rely=0.5, anchor="center")

        self.frame_1 = customtkinter.CTkFrame(master=self)
        self.frame_1.pack(pady=20, padx=40, fill="both", expand=True)

        main_label = customtkinter.CTkLabel(master=self.frame_1, justify=customtkinter.LEFT, text="Visualize csv data",font=customtkinter.CTkFont(size=20, weight="bold"),bg_color="transparent")
        main_label.pack(pady=10, padx=10)

        button_explore = customtkinter.CTkButton(master=self.frame_1, command=lambda: browseFiles(self), text="Browse files")
        button_explore.pack(pady=10, padx=10)

        button_show_graph = customtkinter.CTkButton(master=self.frame_1, command=show_graph, text="Show graph")
        button_show_graph.pack(pady=10, padx=10)

        button_help = customtkinter.CTkButton(master=self.frame_1, command=self.open_toplevel, text="How to use")
        button_help.pack(pady=10, padx=10)

        button_exit = customtkinter.CTkButton(master=self.frame_1, command=quit, text="Exit")
        button_exit.pack(pady=10, padx=10)


    def create_dynamic_checkboxes(self, components_name):
        self.scrollable_frame = customtkinter.CTkScrollableFrame(master=self.frame_1, height=200)
        self.scrollable_frame.pack(fill="both", expand=True)

        scroll_window_label = customtkinter.CTkLabel(master=self.scrollable_frame, justify=customtkinter.LEFT, text="Select what component(s) to visualize",font=customtkinter.CTkFont(size=14, weight="bold"))
        scroll_window_label.pack(pady=10, padx=10)

        for idx, name in enumerate(components_name):
            checkbox_var = IntVar()
            checkbox_1 = customtkinter.CTkCheckBox(master=self.scrollable_frame, text=name, variable=checkbox_var, command=lambda index=idx: self.on_checkbox_change(index))

            checkbox_1.pack(pady=10, padx=10)
            self.checkbox_vars.append(checkbox_var)


    def on_checkbox_change(self,index):

        if self.checkbox_vars[index].get() == 1:
            components_checked.append(index)
        else:
            components_checked.remove(index)


    def open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)
        else:
            self.toplevel_window.focus()

        self.toplevel_window.lift()

    def quit(self):
        if hasattr(self, "dash_app"):
            self.dash_app.server.stop()  # Gracefully stop the Flask server
            time.sleep(1)  # Give the server time to stop
        
        os.kill(os.getpid(), signal.SIGTERM)
        
        


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
