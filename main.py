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
from report import generate_rapport
from convert import convert_csv

logger = setup_logger('main')

# Sets the theme for the UI.
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

HELP_TEXT_FILE = r"UI_componentes\help_text.txt"
HELP_VIDEO_FILE = r"UI_componentes\Tutorial.mp4"
BACKGROUND_IMAGE = r"UI_componentes\backround.jpg"


def browse_files(app_instance):
    """It promts the user to select a csv file
    and adds the csv files to a list for handling and plotting multiple csv data."""


    initial_dir = os.getcwd()

    app_instance.filenames = filedialog.askopenfilenames(
        initialdir=initial_dir,
        title="Select a File",
        filetypes=(("csv files", "*.csv*"), ("all files", "*.*")))
    print(type(app_instance.filenames))

    for names in app_instance.filenames:
        if not names.endswith("csv"):
            messagebox.showinfo("Invalid file type", f"{names} is not a CSV file.")
            return

    check_hmi_type(app_instance, app_instance.filenames)

    return app_instance.filenames


def check_hmi_type(app_instance, filenames):
    """Checks what HMI the user has selected and converts the csv files to the correct format."""

    if app_instance.selected_hmi == "Beijer":
        after_file_selected(app_instance, filenames)
    elif app_instance.selected_hmi == "Siemens":
        converted_csv_list = []
        for filename in filenames:
            converted_csv_list.append(convert_csv(filename))
        after_file_selected(app_instance, converted_csv_list)
    else:
        messagebox.showinfo("Error", "Please select a HMI before trying to make a report")
        return

def after_file_selected(app_instance, filenames):
    """Takes the csv data and makes them into dataframes
    and adds the components to a list for the user to select what to plot."""

    dfs = [pd.read_csv(filename) for filename in filenames]

    combined_df = pd.concat(dfs, ignore_index=True)

    combined_df['Time'] = pd.to_datetime(combined_df['Time'])

    app_instance.data = combined_df
    print(app_instance.data)

    component_set = set()
    for df in dfs:
        component_set.update(df.columns[2:])
    app_instance.components_name = list(component_set)
    logger.info(f"Component names are: {app_instance.components_name}")

    app_instance.create_dynamic_checkboxes(app_instance.components_name)

    return app_instance.data, app_instance.components_name


def create_dash_app(components_name, data, checked):
    """Makes the dash webserver and adds a calaneder and hour slider."""

    logger.info(f"after func dash_app comp names are {components_name}")
    print(components_name)
    print(data)
    print(checked)

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
        #dash_thread.stop()
        dash_thread.start()
        webbrowser.open_new('http://127.0.0.1:8050/')
    except Exception as e:
        logger.error(f"An exception has occures: {e}")


def show_graph(app_instance):
    """Functions that is called when pressing the show graph button."""
    if app_instance.components_checked:
        create_dash_app(app_instance.components_name, app_instance.data, app_instance.components_checked)
        logger.info(f"The data looks like this {app_instance.data}")
        logger.info(f"checkbox pressed index is {app_instance.components_checked}")
        logger.info(f"the csv data contains {app_instance.components_name}")
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
        self.data = None
        self.components_name = []
        self.components_checked = []
        self.filenames = []
        self.selected_hmi = "Beijer"

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

        hmi_drop_list_label = customtkinter.CTkLabel(master=self.frame_1, justify=customtkinter.LEFT,
                                            text="Choose a HMI manufacturer",
                                            font=customtkinter.CTkFont(size=16, weight="bold"),
                                            bg_color="transparent")
        hmi_drop_list_label.pack(pady=10, padx=10)

        self.hmi_drop_list = customtkinter.CTkComboBox(master=self.frame_1,
                                           values=["Beijer", "Siemens"],
                                           command=self.change_hmi,
                                            bg_color="transparent")
        self.hmi_drop_list.pack(pady=10)

        button_explore = customtkinter.CTkButton(master=self.frame_1,
                                                 command=lambda: browse_files(self),
                                                 text="Browse files")
        button_explore.pack(pady=10, padx=10)

        button_show_graph = customtkinter.CTkButton(master=self.frame_1,
                                                    command=lambda: show_graph(self), text="Show graph")
        button_show_graph.pack(pady=10, padx=10)

        button_generate_report = customtkinter.CTkButton(master=self.frame_1,
                                                command=self.start_generate_raport, 
                                                text="Generate a report")

        button_generate_report.pack(pady=10, padx=10)

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
        about_text.pack(pady=30, padx=10)

    def change_hmi(self, selected_option):
        """Changes the HMI to the selected one"""
        self.selected_hmi = selected_option
        logger.info(f"Selected HMI is {self.selected_hmi}")


    def remove_checkboxes(self):
        """Remove all checkboxes and clean up the list."""
        if self.scrollable_frame is not None:
            for child in self.scrollable_frame.winfo_children():
                child.destroy()
                self.checkbox_vars.clear()
                self.components_checked.clear()


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
            self.components_checked.append(index)
        else:
            self.components_checked.remove(index)


    def open_toplevel(self):
        """Opens the how to use page"""
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)
        else:
            self.toplevel_window.focus()
        self.toplevel_window.lift()


    def quit(self):
        """Stops the app/server"""
        os.kill(os.getpid(), signal.SIGTERM)
        # lägg till att ta bort alla convert filerna


    def start_generate_raport(self):
        if self.filenames:
            report_done = generate_rapport(self.filenames)
        else:
            messagebox.showinfo("Error", "Please select a file before trying to make a report")

        if report_done:
            messagebox.showinfo("Info", "The report has been saved")
        else:
            messagebox.showinfo("Error", "There was a error saving the report")

def main():
    """Main func to start the UI"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
    logger.info("Started the program")
