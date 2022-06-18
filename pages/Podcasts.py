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

st.metric(label='Total listening', value=f'{int(df_podcasts.duration.sum())} hours')

st.dataframe(df_podcasts)
