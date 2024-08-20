import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from tkinter import filedialog
from tkinter import Tk
from create_logger import setup_logger

logger = setup_logger("Report")

def generate_rapport(filenames:list) -> bool:
    root = Tk()
    root.withdraw()  # Hide Tkinter root window

    dataframes = []
    for filename in filenames:
        try:
            df = pd.read_csv(filename)
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            root.destroy()
            return False

    # Concatenate all DataFrames along rows
    df = pd.concat(dataframes, ignore_index=True)

    # Ensure 'Time' column is in datetime format
    df['Time'] = pd.to_datetime(df['Time'])

    # Calculate descriptive statistics
    stats = df.describe()

    try:
        file_path = filedialog.asksaveasfilename(defaultextension='.pdf',
                                                 filetypes=[('PDF files', '*.pdf')],
                                                 title='Save report as PDF')
        if not file_path:
            logger.warning("PDF save was cancelled by the user.")
            root.destroy()
            return False
    except Exception as e:
        logger.error(f"Error in file save dialog: {e}")
        root.destroy()
        return False

    pdf_pages = PdfPages(file_path)

    for column in df.columns:
        if column == 'Time' or column == 'Id':
            continue  # Skip non-numerical columns

        fig = plt.figure(figsize=(11.69, 8.27), dpi=100)  # Landscape A4
        sns.lineplot(x=df['Time'], y=df[column], label=column)
        plt.title(f'{column} over time')
        plt.xlabel('')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.2)

        plt.figtext(0.5, 0.01, f'Median value: {stats[column]["50%"]:.3f}\n'
                       f'Lowest value: {stats[column]["min"]:.3f}\n'
                       f'Highest value: {stats[column]["max"]:.3f}\n'
                       f'25% value: {stats[column]["25%"]:.3f}\n'
                       f'75% value: {stats[column]["75%"]:.3f}\n',
            horizontalalignment='center', fontsize=10)

        pdf_pages.savefig(fig)
        plt.close(fig)

    pdf_pages.close()
    root.destroy()
    logger.info(f"Report successfully generated and saved to {file_path}")
    return True
