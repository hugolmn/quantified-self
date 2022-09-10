import os
import streamlit as st
import pandas as pd
from utils import get_cockroachdb_conn


conn = get_cockroachdb_conn('garmin')
df = pd.read_sql('SELECT * FROM stress', conn)
df = df[df.stress >= 0]

st.line_chart(data=df, x='date', y='stress')

df = pd.read_sql('SELECT * FROM hydration', conn).fillna(0)
st.line_chart(data=df.set_index('date'))