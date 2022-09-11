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

st.header(f'Resting Heart Rate (RHR)'
)
rhr_df = get_resting_heart_rate_data(conn)
st.write(f'{len(rhr_df)} days of data collected. RHR is calculated using the lowest 30 minute average in a 24 hour period.')

weekly_rhr = rhr_df.resting_heart_rate.iloc[-7:].mean()
monthly_rhr = rhr_df.resting_heart_rate.iloc[-30:].mean()
quarterly_rhr = rhr_df.resting_heart_rate.iloc[-90:].mean()
all_time_rhr = rhr_df.resting_heart_rate.mean()

# RHR metric plots
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Weekly RHR",
    f"{weekly_rhr:.1f} bpm",
    delta=f"{weekly_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)
col2.metric(
    "Monthly RHR",
    f"{monthly_rhr:.1f} bpm",
    delta=f"{monthly_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)
col3.metric(
    "Quarterly RHR",
    f"{quarterly_rhr:.1f} bpm",
    delta=f"{quarterly_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)
col4.metric(
    "All Time RHR",
    f"{all_time_rhr:.1f} bpm",
    delta=f"{all_time_rhr-all_time_rhr:.1f} bpm vs all time",
    delta_color='inverse'
)

# RHR plots
col1, col2 = st.columns(2)

# 7 day rolling average + scatterplot
rhr_scatterplot = alt.Chart(rhr_df).mark_point().encode(
    x=alt.Y('yearmonthdate(date):T', title='Date'),
    y=alt.Y(
        'resting_heart_rate:Q',
        title='Resting Heart Rate',
        scale=alt.Scale(zero=False)
    ),
    tooltip=['date', 'resting_heart_rate']
).interactive()

rhr_weekly_rolling_mean_plot = alt.Chart(rhr_df).mark_line().transform_window(
    rolling_mean='mean(resting_heart_rate)',
    frame=[-7, 0]
).encode(
    x='yearmonthdate(date):T',
    y=alt.Y('rolling_mean:Q', title='')
)
col1.altair_chart(rhr_scatterplot + rhr_weekly_rolling_mean_plot, use_container_width=True)

# Density plot
rhr_density_all_time = alt.Chart(rhr_df).transform_density(
    'resting_heart_rate',
    as_=['resting_heart_rate', 'density']
).mark_area().encode(
    x=alt.X('resting_heart_rate:Q', title='Resting Heart Rate'),
    y=alt.Y('density:Q', title='Density')
)
col2.altair_chart(rhr_density_all_time, use_container_width=True)
