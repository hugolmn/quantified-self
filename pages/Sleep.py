import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime

from utils import load_css, get_garmin_data

st.set_page_config(layout="wide")
load_css()

def get_sleep_data():
    df = get_garmin_data("""SELECT * FROM sleep""")
    df = df.assign(
        date=pd.to_datetime(df.date, utc=True).dt.tz_convert('Europe/Paris'),
        sleep_end=pd.to_datetime(df.sleep_end, utc=True).dt.tz_convert('Europe/Paris'),
        sleep_start=pd.to_datetime(df.sleep_start, utc=True).dt.tz_convert('Europe/Paris'),
        sleep_duration=pd.to_datetime(df.sleep_time_seconds, unit='s')

    )
    df = df.assign(
        day_of_week=df.date.dt.day_name(),
    )
    return df

def get_sleep_levels_data():
    df = get_garmin_data("""SELECT * FROM sleep_levels""")
    df = df.assign(
        level_start=pd.to_datetime(df.level_start, utc=True).dt.tz_convert('Europe/Paris'),
        level_end=pd.to_datetime(df.level_end, utc=True).dt.tz_convert('Europe/Paris'),
    )

    df = df.assign(activity_level=df.activity_level.map({
            0: 'Deep Sleep',
            1: 'Light Sleep',
            2: 'REM',
            3: 'Awake',
        })
    )

    return df

st.title('Sleep')

sleep = get_sleep_data()

chart = alt.Chart(sleep).mark_point().encode(
    x=alt.X(
        'utchoursminutesseconds(sleep_duration)',
        title='Sleep Duration'
    ),
    y=alt.Y(
        'avg_sleep_stress:Q',
        title='Average Sleep Stress',
        scale=alt.Scale(zero=False)
    ),
    color=alt.Color(
        'sleep_score:Q',
        scale=alt.Scale(scheme='viridis'),
        legend=alt.Legend(orient='top')
    ),
    tooltip=[
        alt.Tooltip('date:T', title='Date'),
        # alt.Tooltip('utchoursminutesseconds(sleep_duration)', title='Sleep duration'),
        alt.Tooltip('avg_sleep_stress:Q', title='Average Sleep Stress', format='.0f'),
        alt.Tooltip('sleep_score:Q', title='Sleep Score'),
    ]
).interactive(bind_y=False, bind_x=False)

st.altair_chart(chart, use_container_width=True, theme='streamlit')

st.header('Sleep activity levels')
sleep_levels = get_sleep_levels_data()

set_same_day_for_all = (lambda dt: 
    dt.replace(year=2022, month=8, day=1) 
    if dt.hour > 12 
    else dt.replace(year=2022, month=8, day=2)
)

sleep_levels = sleep_levels.assign(
    level_start = sleep_levels.level_start.apply(set_same_day_for_all),
    level_end = sleep_levels.level_end.apply(set_same_day_for_all)
)

chart = alt.Chart(sleep_levels).mark_bar().encode(
    y=alt.Y(
        'yearmonthdatehoursminutesseconds(level_start):T',
        axis=alt.Axis(
            format='%H:%M',
            title='Time'
        )
    ),
    y2=alt.Y2(
        'yearmonthdatehoursminutesseconds(level_end):T',
    ),
    x=alt.X('date'),
    color=alt.Color(
        'activity_level',
        title='Activity Level',
        scale=alt.Scale(
            domain=[
                'Deep Sleep',
                'Light Sleep',
                'REM',
                'Awake'
            ],
            range=[
                '#004ba0',
                '#1976d2',
                '#ac06bc',
                '#ed79d5',
            ]
        )
    ),
    tooltip=[
        alt.Tooltip('date'),
        alt.Tooltip('hoursminutes(level_start):T', title='Level Start'),
        alt.Tooltip('hoursminutes(level_end):T', title='Level End'),
        alt.Tooltip('activity_level', title='Activity Level'),
    ]
)
st.altair_chart(chart, use_container_width=True, theme='streamlit')
