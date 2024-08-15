"""
Converts a CSV file from siemens to the default format "Beijer".
"""

import pandas as pd

def convert_csv_siemens(input_file_path):
    output_file_path = input_file_path.replace('.csv', '_temp_converted.csv')
    df = pd.read_csv(input_file_path, sep=';', decimal=',', on_bad_lines="skip")

    unwanted_var_names = ['$RT_DIS$', '$RT_OFF$']
    df = df[~df['VarName'].isin(unwanted_var_names)]

    df['VarValue'] = df['VarValue'].astype(str).str.replace(',', '.').astype(float)

    pivot_df = df.pivot_table(index='TimeString', columns='VarName', values='VarValue', aggfunc='first')

    pivot_df = pivot_df.reset_index()
    pivot_df.insert(0, 'Id', range(1, 1 + len(pivot_df)))

    pivot_df.rename(columns={'TimeString': 'Time'}, inplace=True)

    pivot_df.to_csv(output_file_path, index=False)

    return output_file_path
