"""Main program to visualize csv data, can be tested on the example data in the folder "data" 
Made by Roberts Balulis"""

import time
from tkinter import IntVar, filedialog, messagebox
import threading
import os
from os import startfile
import signal
import webbrowser

import customtkinter
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from PIL import Image
from waitress import serve

from create_log import setup_logger

logger = setup_logger('main')

# Sets the theme for the UI.
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

HELP_TEXT_FILE = r"UI_componentes\help_text.txt"
HELP_VIDEO_FILE = r"UI_componentes\Tutorial.mp4"
BACKGROUND_IMAGE = r"UI_componentes\backround.jpg"

components_checked = []


def browse_files(app_instance):
    """It promts the user to select a csv file
    and adds the csv files to a list for handling and plotting multiple csv data."""

    if hasattr(app_instance, "dash_app"):
        app_instance.dash_app.server.stop()
        time.sleep(1)

    initial_dir = os.getcwd()

    filenames = filedialog.askopenfilenames(
        initialdir=initial_dir,
        title="Select a File",
        filetypes=(("csv files", "*.csv*"), ("all files", "*.*")))

    for names in filenames:
        if not names.endswith("csv"):
            messagebox.showinfo("Invalid file type", f"{names} is not a CSV file.")
            return

    after_file_selected(app_instance, filenames)

    return filenames


def after_file_selected(app_instance, filenames):
    """Takes the csv data and makes them into dataframes
    and adds the componentes to a list for the user to select what to plot."""
    global data
    global components_name
    dfs = []

    for filename in filenames:  # Makes possible to select multiple csv files
        dataframe = pd.read_csv(filename)
        dfs.append(dataframe)
    data = pd.concat(dfs, axis=0, ignore_index=True)

    data = data.dropna()

    data['Time'] = pd.to_datetime(data['Time'])

    components_name = []

    components_name = pd.read_csv(filename, index_col=0, nrows=0).columns.tolist()
    components_name = components_name[1:]
    logger.info(f"component name in afterfile selected is {components_name}")

    # Makes checkboxes in the UI for each component in the csv file.
    app_instance.create_dynamic_checkboxes(components_name)

    return data, components_name


def create_dash_app(components_name, data, checked):
    """Makes the dash webserver and adds a calaneder and hour slider."""
    logger.info(f"after func dash_app comp names are {components_name}")

    app = dash.Dash(__name__)
    # Calender so the user can select what date to see the plottet data
    app.layout = html.Div([
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed=data['Time'].min().date(),
            max_date_allowed=data['Time'].max().date(),
            initial_visible_month=data['Time'].min().date(),
            start_date=data['Time'].min().date(),
            end_date=data['Time'].max().date(),

        ),
        # Hour slider so the user can select the hour of the day to see the plottet data.
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
        """Updates graph when the user changes the date or time."""
        try:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            start_time = start_date.replace(hour=hour_range[0])
            end_time = end_date.replace(hour=hour_range[1])

            filtered_data = data[(data['Time'] >= start_time) & (data['Time'] <= end_time)]

            logger.info(f"componentes name after updating date is {components_name}")

            selected_columns = [components_name[i] for i in checked]
            logger.info(f"plotted data after updating date is {selected_columns}")
            fig = px.line(filtered_data, x='Time', y=selected_columns)

        except Exception as e:
            logger.error(f"An error occured {e}")

        return fig
    try:
        # Starts the webserver with waitress.
        logger.info(f"Trying to start the webserver")
        dash_thread = threading.Thread(target=serve, args=(app.server,),
                                       kwargs={'host': '127.0.0.1', 'port': 8050, '_quiet': True})
        dash_thread.daemon = True
        dash_thread.start()
        webbrowser.open_new('http://127.0.0.1:8050/')
    except Exception as e:
        logger.error(f"An exception has occures: {e}")


def show_graph():
    """Functions that is called when pressing the show graph button."""
    if components_checked:
        create_dash_app(components_name, data, components_checked)
        logger.info(f"The data looks like this {data}")
        logger.info(f"checkbox pressed index is {components_checked}")
        logger.info(f"the csv data contains {components_name}")
    else:
        messagebox.showinfo("No component selected", "Please select atleast one component to plot.")


class ToplevelWindow(customtkinter.CTkToplevel):
    """Class for the how to use window with the video tutorial."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("700x300")
        self.resizable(False, False)
        self.title("Csv visualizer")

        with open(HELP_TEXT_FILE, "r", encoding="utf-8") as text_file:
            help_text = text_file.read()

        self.label = customtkinter.CTkLabel(self, text=help_text, justify="left")
        self.label.pack(padx=20, pady=20)

        self.button_show_graph = customtkinter.CTkButton(master=self,
                                                         command=self.play_video,
                                                         text="See video tutorial")
        self.button_show_graph.pack(pady=10, padx=10)

        self.attributes('-topmost', True)


    def play_video(self):
        """Plays the tutorial video"""
        startfile(HELP_VIDEO_FILE)


class App(customtkinter.CTk):
    """Class for the main app and main window"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.checkbox_vars = []
        self.toplevel_window = None
        self.scrollable_frame = None

        self.geometry("400x700")
        self.title("Csv visualizer")

        self.resizable(False, False)

        self.bg_image = customtkinter.CTkImage(Image.open(BACKGROUND_IMAGE),
                                               size=(400, 980))
        
        self.bg_image_label = customtkinter.CTkLabel(self, image=self.bg_image)
        self.bg_image_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.frame_1 = customtkinter.CTkFrame(master=self, bg_color="transparent")
        self.frame_1.place(relx=0.5, rely=0.5, anchor="center")

        self.frame_1 = customtkinter.CTkFrame(master=self)
        self.frame_1.pack(pady=20, padx=40, fill="both", expand=True)

        main_label = customtkinter.CTkLabel(master=self.frame_1, justify=customtkinter.LEFT,
                                            text="Csv visualizer",
                                            font=customtkinter.CTkFont(size=20, weight="bold"),
                                            bg_color="transparent")
        main_label.pack(pady=10, padx=10)

        button_explore = customtkinter.CTkButton(master=self.frame_1,
                                                 command=lambda: browse_files(self),
                                                 text="Browse files")
        button_explore.pack(pady=10, padx=10)

        button_show_graph = customtkinter.CTkButton(master=self.frame_1,
                                                    command=show_graph, text="Show graph")
        button_show_graph.pack(pady=10, padx=10)

        button_help = customtkinter.CTkButton(master=self.frame_1,
                                              command=self.open_toplevel, text="How to use")
        button_help.pack(pady=10, padx=10)

        button_exit = customtkinter.CTkButton(master=self.frame_1,
                                              command=self.quit, text="Exit")
        button_exit.pack(pady=10, padx=10)

        about_text = customtkinter.CTkLabel(master=self.frame_1,
                                            font=customtkinter.CTkFont(size=16, weight="bold"),
                                            bg_color="transparent",
                                            text="Owned and made by Roberts Balulis")
        about_text.pack(pady=70, padx=10)


    def remove_checkboxes(self):
        """Remove all checkboxes and clean up the list."""
        if self.scrollable_frame is not None:
            for child in self.scrollable_frame.winfo_children():
                child.destroy()
                self.checkbox_vars.clear()
                components_checked.clear()


    def create_dynamic_checkboxes(self, components_name):
        """Makes checkboxes depending of how many componentes are in the csv file."""
        self.remove_checkboxes()
        if self.scrollable_frame is None:  # Create the scrollable_frame if it doesn't exist yet
            self.scrollable_frame = customtkinter.CTkScrollableFrame(master=self.frame_1, height=200)
            self.scrollable_frame.pack(fill="both", expand=True)

        scroll_window_label = customtkinter.CTkLabel(master=self.scrollable_frame,
                                                     justify=customtkinter.LEFT,
                                                     text="Select what component(s) to visualize",
                                                     font=customtkinter.CTkFont(size=14,
                                                                                weight="bold"))
        scroll_window_label.pack(pady=10, padx=10)

        for idx, name in enumerate(components_name):
            checkbox_var = IntVar()
            checkbox_1 = customtkinter.CTkCheckBox(master=self.scrollable_frame, text=name,
                                                   variable=checkbox_var,
                                                   command=lambda index=idx:
                                                   self.on_checkbox_change(index))

            checkbox_1.pack(pady=10, padx=10)
            self.checkbox_vars.append(checkbox_var)
           

    def on_checkbox_change(self, index):
        """Makes a list for every checkbox that is crossed."""
        if self.checkbox_vars[index].get() == 1:
            components_checked.append(index)
        else:
            components_checked.remove(index)


    def open_toplevel(self):
        """Opens the how to use page"""
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)
        else:
            self.toplevel_window.focus()
        self.toplevel_window.lift()


    def quit(self):
        """Stops the app/server"""
        if hasattr(self, "dash_app"):
            self.dash_app.server.stop()
            time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)


def main():
    """Main func to start the UI"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
    logger.info("Started the program")
