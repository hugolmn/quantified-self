import streamlit as st
from gsheetsdb import connect
import pandas as pd

st.title("Podcasts")

# Create a connection object.
con = connect()

sheet_podcasts = st.secrets['podcasts']
df_podcasts = pd.read_sql_query(
  f'SELECT * FROM "{sheet_podcasts}"',
  con,
  parse_dates=['playbackDate']
)

total, episodes, podcasts = st.columns(3)
total.metric(label='Total listening', value=f'{int(df_podcasts.duration.sum())} hours')
episodes.metric(label='#Episodes' value=len(df_podcasts))
podcasts.metric(label='#Podcasts' value=df_podcasts.podcasts.nunique())

st.bar_chart(df_podcasts.groupby(df_podcasts.playbackDate.dt.year).duration.sum())
st.dataframe(df_podcasts)
