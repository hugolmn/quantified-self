import os
import streamlit as st
import pandas as pd
from utils import get_cockroachdb_conn

certificate_path = os.path.expanduser('~/.postgresql/root.crt')
if not os.path.exists(certificate_path):
    os.system(f"curl --create-dirs -o ~/.postgresql/root.crt -O {st.secrets['get_certificate_cockroachdb']}")

import glob
glob.glob('$HOME')

conn = get_cockroachdb_conn('garmin')
df = pd.read_sql('SELECT * FROM stress', conn)
df = df[df.stress >= 0]

st.line_chart(data=df, x='date', y='stress')

df = pd.read_sql('SELECT * FROM hydration', conn).fillna(0)
st.line_chart(data=df.set_index('date'))