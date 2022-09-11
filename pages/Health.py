import os
import streamlit as st
import pandas as pd
import altair as alt

from utils import get_cockroachdb_conn

st.set_page_config(layout="wide")
conn = get_cockroachdb_conn('garmin')

def get_resting_heart_rate_data(conn):
    return pd.read_sql("""SELECT date, resting_heart_rate FROM stats""", conn)

st.title('Health')
st.header('Resting Heart Rate (RHR)')
st.write('RHR is calculated using the lowest 30 minute average in a 24 hour period.')
rhr_df = get_resting_heart_rate_data(conn)

weekly_rhr = rhr_df.resting_heart_rate.iloc[-7:].mean()
monthly_rhr = rhr_df.resting_heart_rate.iloc[-30:].mean()
quarterly_rhr = rhr_df.resting_heart_rate.iloc[-90:].mean()
all_time_rhr = rhr_df.resting_heart_rate.mean()

st.dataframe(rhr_df.iloc[-7:])

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Weekly RHR",
    f"{weekly_rhr:.1f} beats/min",
    delta=f"{weekly_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)
col2.metric(
    "Monthly RHR",
    f"{monthly_rhr:.1f} beats/min",
    delta=f"{monthly_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)
col3.metric(
    "Quarterly RHR",
    f"{quarterly_rhr:.1f} beats/min",
    delta=f"{quarterly_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)
col4.metric(
    "All Time RHR",
    f"{all_time_rhr:.1f} beats/min",
    delta=f"{all_time_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)

rhr_scatterplot = alt.Chart(rhr_df).mark_point().encode(
    x='date:T',
    y='resting_heart_rate:Q'
)
rhr_weekly_rolling_mean_plot = alt.Chart(rhr_df).mark_line().transform_window(
    rolling_mean='mean(resting_heart_rate)',
    frame=[-7, 0]
).encode(
    x='date:T',
    y='rolling_mean:Q'
)
st.altair_chart(rhr_scatterplot + rhr_weekly_rolling_mean_plot)
