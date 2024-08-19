import time
from tkinter import IntVar, filedialog, messagebox
import os
import webbrowser
import multiprocessing
import sys

import customtkinter
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from PIL import Image

from create_logger import setup_logger
from report import generate_rapport
from convert_csv import convert_csv_siemens


HELP_TEXT_FILE = r"UI_componentes\help_text.txt"
HELP_VIDEO_FILE = r"UI_componentes\Tutorial.mp4"
BACKGROUND_IMAGE = r"UI_componentes\background.jpg"
HOST = '127.0.0.1'
PORT = 8050
URL = f'http://{HOST}:{PORT}'

# So the exe wont crash without a console.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')


class APP(customtkinter.CTk):
    """Class for the main gui window."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        self.checkbox_vars = []
        self.toplevel_window = None
        self.scrollable_frame = None
        self.data = None
        self.components_name = []
        self.components_checked = []
        self.filenames = []
        self.selected_hmi = "Beijer"
        self.server_process = None

        self.geometry("400x750")
        self.title("Csv visualizer")

        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.disable_close_button)

        self.bg_image = customtkinter.CTkImage(Image.open(BACKGROUND_IMAGE), size=(400, 980))

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
                                            text="Made by Roberts Balulis")
        about_text.pack(pady=30, padx=10)


    def disable_close_button(self):
        """Disables the x button on top right so the user uses the exit button."""
        pass


    def change_hmi(self, selected_option):
        """Changes the HMI to the selected one."""
        self.selected_hmi = selected_option
        logger.info(f"Selected HMI is {self.selected_hmi}")


    def remove_checkboxes(self):
        """Remove all checkboxes and clean up the list."""
        if self.scrollable_frame is not None:
            for child in self.scrollable_frame.winfo_children():
                child.destroy()
                self.checkbox_vars.clear()
                self.components_checked.clear()


    def create_checkboxes(self, components_name):
        """Creates checkboxes depending on how many components are in the CSV file."""
        self.remove_checkboxes()
        if self.scrollable_frame is None:
            self.scrollable_frame = customtkinter.CTkScrollableFrame(master=self.frame_1, height=200)
            self.scrollable_frame.pack(fill="both", expand=True)

        scroll_window_label = customtkinter.CTkLabel(master=self.scrollable_frame,
                                                     justify=customtkinter.LEFT,
                                                     text="Select what component(s) to visualize",
                                                     font=customtkinter.CTkFont(size=14, weight="bold"))
        scroll_window_label.pack(pady=10, padx=10)

        for idx, name in enumerate(components_name):
            checkbox_var = IntVar()
            checkbox_1 = customtkinter.CTkCheckBox(master=self.scrollable_frame, text=name,
                                                   variable=checkbox_var,
                                                   command=lambda index=idx: self.on_checkbox_change(index))

            checkbox_1.pack(pady=10, padx=10)
            self.checkbox_vars.append(checkbox_var)


    def on_checkbox_change(self, index):
        """Makes a list for every checkbox that is selected."""
        if self.checkbox_vars[index].get() == 1:
            self.components_checked.append(index)
        else:
            self.components_checked.remove(index)


    def open_toplevel(self):
        """Opens the how-to-use page."""
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)
        else:
            self.toplevel_window.focus()
        self.toplevel_window.lift()


    def quit(self):
        """Stops the app/server."""
        if self.server_process:
            self.stop_server()

        if self.selected_hmi != "Beijer" and self.filenames:
            folder_paths = set(os.path.dirname(file) for file in self.filenames)
            folder_list = "\n".join(folder_paths)
            messagebox.showinfo("Error", f"There are some temporary files that need to be deleted in the following folder(s):\n{folder_list}")
        self.destroy()


    def stop_server(self):
        """Stops the running Dash webserver by terminating its process."""
        if self.server_process is not None and self.server_process.is_alive():
            logger.info("Terminating Dash server process.")
            self.server_process.terminate()
            self.server_process.join()
            self.server_process = None
            logger.info("Dash server process terminated.")


    def start_generate_raport(self):
        if not self.filenames:
            return messagebox.showinfo("Error", "Please select a file before trying to make a report")

        try:
            if self.selected_hmi == "Beijer":
                report_done = generate_rapport(self.filenames)
            elif self.selected_hmi == "Siemens":
                converted_files = (convert_csv_siemens(filename) for filename in self.filenames)
                report_done = generate_rapport(converted_files)
            else:
                raise ValueError("Unsupported HMI selected")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            messagebox.showinfo("Error", f"Failed to generate report: {str(e)}")
            return

        messagebox.showinfo("Info", "The report has been saved" if report_done else "There was an error saving the report")



def browse_files(app_instance:APP):
    """Prompts the user to select a CSV file and handles the selection."""
    app_instance.stop_server()
    initial_dir = os.getcwd()

    app_instance.filenames = filedialog.askopenfilenames(
        initialdir=initial_dir,
        title="Select a File",
        filetypes=(("csv files", "*.csv*"), ("all files", "*.*"))
    )

    if not app_instance.filenames:
        return

    for names in app_instance.filenames:
        if not names.endswith("csv"):
            messagebox.showinfo("Invalid file type", f"{names} is not a CSV file.")
            return

    check_hmi_type(app_instance, app_instance.filenames)

    return app_instance.filenames


def check_hmi_type(app_instance:APP, filenames):
    """Checks what HMI the user has selected and converts the CSV files to the correct format."""
    if app_instance.selected_hmi == "Beijer":
        after_file_selected(app_instance, filenames)
    elif app_instance.selected_hmi == "Siemens":
        converted_csv_list = []
        for filename in filenames:
            converted_csv_list.append(convert_csv_siemens(filename))
        after_file_selected(app_instance, converted_csv_list)
    else:
        messagebox.showinfo("Error", "Please select an HMI before trying to make a report")
        return

def after_file_selected(app_instance:APP, filenames):
    """Takes the CSV data, makes them into DataFrames, and adds components to a list for plotting."""
    dataframes = [pd.read_csv(filename) for filename in filenames]
    combined_df = pd.concat(dataframes, ignore_index=True)
    combined_df['Time'] = pd.to_datetime(combined_df['Time'])

    app_instance.data = combined_df
    component_set = set()
    for dataframe in dataframes:
        component_set.update(dataframe.columns[2:])
    app_instance.components_name = list(component_set)
    logger.info(f"Component names are: {app_instance.components_name}")

    app_instance.create_checkboxes(app_instance.components_name)

    return app_instance.data, app_instance.components_name


def run_dash_server(data, components_name, checked):
    """Runs the Dash server in a separate process."""
    dash_app = dash.Dash(__name__)

    dash_app.layout = html.Div([
        dcc.DatePickerRange(
            id='date-range-picker',
            min_date_allowed=data['Time'].min().date(),
            max_date_allowed=data['Time'].max().date(),
            initial_visible_month=data['Time'].min().date(),
            start_date=data['Time'].min().date(),
            end_date=data['Time'].max().date(),
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
        dcc.Loading(
            id="loading-1",
            type="default",
            children=[
                dcc.Graph(id='line-graph', style={'width': '100%', 'height': '85vh'})
            ]
        )
    ])

    @dash_app.callback(
        Output('hour-range-slider-output', 'children'),
        [Input('hour-range-slider', 'value')]
    )
    def update_output(value):
        return f'Selected hour range: {value[0]}:00 - {value[1]}:00'

    @dash_app.callback(
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

            selected_columns = [components_name[i] for i in checked]
            fig = px.line(filtered_data, x='Time', y=selected_columns)

        except Exception as exception:
            logger.error(f"An error occurred {exception}")
            fig = {}

        return fig

    dash_app.logger.disabled = True
    dash_app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def create_dash_app(app_instance:APP, components_name, data, checked):
    """Creates the Dash webserver and starts it in a separate process."""
    server_process = multiprocessing.Process(target=run_dash_server, args=(data, components_name, checked))
    server_process.start()
    app_instance.server_process = server_process
    time.sleep(5)  # Wait for the server to start before opening the webbrowser
    webbrowser.open_new(URL)


def show_graph(app_instance:APP):
    """Function that is called when pressing the show graph button."""
    if app_instance.components_checked:
        create_dash_app(app_instance, app_instance.components_name,
                        app_instance.data, app_instance.components_checked)
        logger.info(f"The data looks like this {app_instance.data}")
        logger.info(f"Checkbox pressed index is {app_instance.components_checked}")
        logger.info(f"The CSV data contains {app_instance.components_name}")
    else:
        messagebox.showinfo("No component selected", "Please select at least one component to plot.")


class ToplevelWindow(customtkinter.CTkToplevel):
    """Class for the how-to-use window with the video tutorial."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("750x300")
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
        """Plays the tutorial video."""
        os.startfile(HELP_VIDEO_FILE)


def main():
    """Main function to start the UI."""
    app = APP()
    app.mainloop()


if __name__ == "__main__":
    # Needed for the exe to work or else the multiprocessing will start multiple instances of the app.
    multiprocessing.freeze_support()
    logger = setup_logger('main')
    logger.info("Started the program")
    main()
