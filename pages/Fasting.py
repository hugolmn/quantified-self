import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import io
import datetime
from utils import find_file_id, download_file, get_garmin_data, load_css

st.set_page_config(layout="wide")
load_css()

@st.cache
def load_fasting_df():
    # Find and download file
    file_id = find_file_id("name contains 'zero.csv'")[0]['id']
    file = download_file(file_id=file_id)

    # Load as dataframe
    df = pd.read_csv(io.StringIO(file.getvalue().decode()))

    # Convert to datetime
    df['End'] = (pd.to_datetime(df.Date + ' ' + df.End) + pd.Timedelta('1D')).dt.tz_localize('Europe/Paris')
    df['Start'] = pd.to_datetime(df.Date + ' ' + df.Start).dt.tz_localize('Europe/Paris')

    # Add fast duration
    df['fast_duration_sec'] = (df.End - df.Start).dt.seconds

    # Sort by date
    df = df.sort_values(by='Start')

    # Drop most recent one: unfinished fast
    df = df.iloc[:-1]

    # Drop some columns
    df = df.drop(columns=['Night Eating', 'Hours'])
    return df

def load_stress_df():
    stress = get_garmin_data("SELECT * FROM stress")
    stress = stress.assign(date=pd.to_datetime(stress.date, utc=True).dt.tz_convert('Europe/Paris'))
    return stress

def load_fasting_stress_df():
    df = load_fasting_df()

    stress = get_garmin_data("SELECT * FROM stress")
    stress = stress.assign(date=pd.to_datetime(stress.date, utc=True).dt.tz_convert('Europe/Paris'))

    df = pd.merge(
        left=stress,
        right=df.drop(columns=['Start']),
        left_on=stress['date'].dt.date,
        right_on=df.End.dt.date,
        
    ).drop(columns=['key_0'])
    df['time_since_breakfast'] = ((df['date'] - df['End']) / pd.Timedelta('1H')).round(1)
    return df

def load_fasting_heart_rate_df():
    df = load_fasting_df()

    stress = get_garmin_data("SELECT * FROM heart_rate")
    stress = stress.assign(date=pd.to_datetime(stress.date, utc=True).dt.tz_convert('Europe/Paris'))

    df = pd.merge(
        left=stress,
        right=df.drop(columns=['Start']),
        left_on=stress['date'].dt.date,
        right_on=df.End.dt.date,
        
    ).drop(columns=['key_0'])
    df['time_since_breakfast'] = ((df['date'] - df['End']) / pd.Timedelta('1H')).round(1)
    return df

def format_timedelta(seconds):
    return str(
        datetime.timedelta(
            seconds=seconds.round()
        )
    )[:-3].replace(':', 'h ') + 'min'

def generate_metric_fasting(col, label, df, days):
    if days:
        fast = df.sort_values(by='Start').iloc[-days:].fast_duration_sec.mean()
        all_time = df.fast_duration_sec.mean()
    else:
        fast = df.fast_duration_sec.mean()
    
    return col.metric(
        label,
        value=format_timedelta(fast),
        delta=f"""{format_timedelta(fast - all_time)} vs all time""" if days is not None else None,
    )

st.title('Fasting')
df = load_fasting_df()

steps_metrics = {
    'Week': 7,
    'Month': 30,
    'Year': 365,
    'All Time': None
}
for params, col in zip(steps_metrics.items(), st.columns(4)):
    generate_metric_fasting(col, params[0], df, params[1])

