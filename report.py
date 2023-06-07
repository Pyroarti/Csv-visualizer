import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

df = pd.read_csv('Flow_log.csv')

df['Time'] = pd.to_datetime(df['Time'])

stats = df.describe()

max_days = df.idxmax()

pdf_pages = PdfPages('output.pdf')

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
    plt.yticks([])

    plt.figtext(0.5, 0.01, f'Median: {stats[column]["50%"]}\n'
                           f'Min: {stats[column]["min"]}\n'
                           f'Max: {stats[column]["max"]}\n'
                           f'Day of max value: {max_days[column]}', 
                horizontalalignment='center')

    pdf_pages.savefig(fig)

pdf_pages.close()
