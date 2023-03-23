import plotly.express as px
import pandas as pd

df = pd.read_csv("Pws_loggning-main\data\Pressure_log.csv")
df['Time'] = pd.to_datetime(df['Time'])

fig = px.line(df, x="Time", y=["MP01", "MP02", "MP03"])
fig.show()
