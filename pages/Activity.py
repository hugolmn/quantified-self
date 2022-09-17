import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

from utils import get_cockroachdb_conn, load_css, get_garmin_data

st.set_page_config(layout="wide")
load_css()

def get_steps_detailed_data():
    df = get_garmin_data("""SELECT * FROM steps""")
    df = df.assign(date=pd.to_datetime(df.date, utc=True).dt.tz_convert('Europe/Paris'))
    df['day_of_week'] = np.where(df.date.dt.weekday >= 6, 'weekend', 'weekday')
    return df

def get_steps_daily_data():
    df = get_garmin_data("""SELECT date, total_steps FROM stats""")
    return df

st.title('Activity')

st.header(f'Steps')
steps_df = get_steps_detailed_data()
steps_daily_df = get_steps_daily_data()

weekly_steps = steps_daily_df.total_steps.iloc[-7:].mean()
monthly_steps = steps_daily_df.total_steps.iloc[-30:].mean()
quarterly_steps = steps_daily_df.total_steps.iloc[-90:].mean()
all_time_steps = steps_daily_df.total_steps.mean()

# RHR metric plots
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Week",
    f"{weekly_steps/1000:.1f}k/day",
    delta=f"{(weekly_steps-all_time_steps)/1000:.1f}k vs all time",
)
col2.metric(
    "Month",
    f"{monthly_steps/1000:.1f}k/day",
    delta=f"{(monthly_steps-all_time_steps)/1000:.1f}k vs all time",
)
col3.metric(
    "Quarter",
    f"{quarterly_steps/1000:.1f}k/day",
    delta=f"{(quarterly_steps-all_time_steps)/1000:.1f}k vs all time",
)
col4.metric(
    "All Time",
    f"{all_time_steps/1000:.1f}k/day",
)

# Steps plots
col1, col2 = st.columns(2)

# 7 day rolling average + scatterplot
daily_steps = steps_df.groupby(steps_df['date'].dt.date, group_keys=False).sum().reset_index()

steps_scatterplot_daily = alt.Chart(daily_steps).mark_bar(color=st.secrets["theme"]['primaryColor']).encode(
    x=alt.Y('yearmonthdate(date):T', title='Date'),
    y=alt.Y(
        'steps:Q',
        title='Daily Steps',
    ),
    tooltip=['date', 'steps']
).interactive()

steps_weekly_rolling_mean_plot = alt.Chart(daily_steps).mark_line(color=st.secrets["theme"]['secondaryColor']).transform_window(
    rolling_mean='mean(steps)',
    frame=[-7, 0]
).encode(
    x='yearmonthdate(date):T',
    y=alt.Y('rolling_mean:Q', title='')
)

col1.altair_chart(steps_scatterplot_daily + steps_weekly_rolling_mean_plot, use_container_width=True)

# Hourly plot
steps_scatterplot_hourly = alt.Chart(steps_df).mark_line().encode(
    x=alt.Y('hoursminutes(date):T', title='Time'),
    y=alt.Y(
        'mean(steps):Q',
        title='Hourly Steps',
    ),
    color=alt.Color(
        'day_of_week:N',
        title="Day of week",
        scale=alt.Scale(
            range=[
                st.secrets["theme"]['primaryColor'],
                st.secrets["theme"]['secondaryColor']
            ]
        ),
    ),
    tooltip=['hoursminutes(date)']
).interactive()

col2.altair_chart(steps_scatterplot_hourly, use_container_width=True)


st.header(f'Activity Level')

col1, col2 = st.columns(2)

activity_level_chart = alt.Chart(steps_df).mark_bar().encode(
    x=alt.X('yearmonthdate(date)', title='Date'),
    y=alt.Y('count(activity_level)', stack='normalize', title='Percentageof day'),
    color=alt.Color('activity_level:N', title='Activity level'),
    tooltip=[
        alt.Tooltip('yearmonthdate(date)', title='Date'),
        alt.Tooltip('activity_level', title='Activity level'),
    ]
)

col1.altair_chart(activity_level_chart, use_container_width=True)