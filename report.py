import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from tkinter import filedialog
from tkinter import Tk

from create_log import setup_logger

logger = setup_logger('Report')

def generate_rapport(filenames):
    root = Tk()
    root.withdraw()

    dataframes = []
    for filename in filenames:
        df = pd.read_csv(filename)
        dataframes.append(df)

    df['Time'] = pd.to_datetime(df['Time'])

    stats = df.describe()

    max_days = df.idxmax()
    try:
        file_path = filedialog.asksaveasfilename(defaultextension='.pdf')
    except Exception as e:
        logger.error(e)

    pdf_pages = PdfPages(file_path)

    for column in df.columns:
        if column == 'Time' or column == 'Id':
            continue  # Skip non numerical columns

        fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
        plt.plot(df['Time'], df[column], label=column)
        plt.title(f'{column} over time')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True)
        plt.xticks([])
        plt.subplots_adjust(bottom=0.55)

        plt.figtext(0.5, 0.01, f'Median: {stats[column]["50%"]}\n'
                               f'Min: {stats[column]["min"]}\n'
                               f'Max: {stats[column]["max"]}\n'
                               f'25%: {stats[column]["25%"]}\n'
                               f'75%: {stats[column]["75%"]}\n', 
                    horizontalalignment='center', fontsize= 30.0)

        pdf_pages.savefig(fig)

    pdf_pages.close()

    return True
