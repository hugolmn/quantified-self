import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import io
import datetime
from utils import find_file_id, download_file, get_garmin_data, load_css
st.set_page_config(layout="wide")
load_css()

@st.cache_data
def load_fasting_df():
    # Find and download file
    file_id = find_file_id("name contains 'zero.csv'")[0]['id']
    file = download_file(file_id=file_id)

    # Load as dataframe
    df = pd.read_csv(io.StringIO(file.getvalue().decode()))

    # Drop when fast is less than an hour
    df = df[df.Hours != 0]

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
    df['time_since_breakfast'] = ((df['date'] - df['End']).dt.ceil('5T') / pd.Timedelta('1H'))
    return df

def format_timedelta(seconds):
    if seconds >= 0:
        return f"{seconds // 3600:.0f}h {(seconds // 60) % 60:.0f}min "
    seconds = abs(seconds)
    if seconds < 3600:
        return f"-{(seconds // 60) % 60:.0f}min "
    return f"-{seconds // 3600:.0f}h {(seconds // 60) % 60:.0f}min"

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

def breakfast_chart(df_fasting_stress, min_hour=0, max_hour=24):
    df_fasting_stress = df_fasting_stress[df_fasting_stress.time_since_breakfast.between(-3, 3)]

    # Filter by fast end date
    df_fasting_stress = df_fasting_stress[df_fasting_stress.End.dt.hour.between(min_hour, max_hour)]

    df_fasting_stress = pd.pivot_table(
            df_fasting_stress[df_fasting_stress.stress > 0],
            index=df_fasting_stress.time_since_breakfast.mul(6).round(0).div(6),
            values='stress',
            aggfunc='median'
        ).reset_index()

    fasting_stress_chart = alt.Chart(
        df_fasting_stress
    ).mark_line(
        color=st.secrets["theme"]['primaryColor']
    ).encode(
        x=alt.X('time_since_breakfast:Q', title='Hours since breakfast'),
        y=alt.Y('median(stress):Q', title='Median stress level', scale=alt.Scale(zero=False))
    )

    rule = alt.Chart(
        pd.DataFrame({'time_since_breakfast': [0]}).assign(legend='Breaking fast')
    ).mark_rule().encode(
    x='time_since_breakfast:Q',
    color=alt.Color(
        'legend:N',
        title='',
        scale=alt.Scale(
            range=[
                st.secrets["theme"]['secondaryColor'],
                st.secrets["theme"]['secondaryColor']
            ]
        ),
        legend=alt.Legend(orient='bottom-right')
    )
    )

    st.altair_chart(fasting_stress_chart + rule, use_container_width=True, theme='streamlit')

st.title('Fasting')
df = load_fasting_df()
st.write(f'I am an adept of intermittent fasting: I usually skip breakfast and spend around 16 hours a day fasting. {len(df)} days of data collected.')

steps_metrics = {
    'Week': 7,
    'Month': 30,
    'Year': 365,
    'All Time': None
}
for params, col in zip(steps_metrics.items(), st.columns(4)):
    generate_metric_fasting(col, params[0], df, params[1])

st.header('Fasting history')
df = df.assign(
    fast_duration_hours=df.fast_duration_sec / (60*60),
    tooltip=df.fast_duration_sec.apply(format_timedelta)
)
df = df.assign(
    color=pd.cut(
        df.fast_duration_hours,
        bins=[0, 12, 14, 16, np.inf],
        labels=['<12H', '<14H', '<16H', '>16H'],
        right=False
    )
)
fasting_history = alt.Chart(df).mark_rect().encode(
    x=alt.X('date(Date):O', title='Day'),
    y=alt.Y('yearmonth(Date):O', title='Month'),
    color=alt.Color(
        'color:N',
        title='Fasting hours',
        scale=alt.Scale(
            reverse=True,
            range=['#3B97F3', '#FFB154', '#F27716', '#DE5809'],
        )
    ),
    tooltip=[
        alt.Tooltip('yearmonthdate(Date):T', title='Date'),
        alt.Tooltip('tooltip', title='Fast duration')
    ]
)
st.altair_chart(fasting_history, use_container_width=True, theme='streamlit')


st.header('Impact of breaking fast on stress level')
df_fasting_stress = load_fasting_stress_df()
st.write(f"""
    Breaking a fast (or any meal in general) has a strong impact on the stress level.
    Graphs based on {df_fasting_stress.Date.nunique()} days of data.
    If the first meal is taken after 11AM, a spike follows:
""")
breakfast_chart(df_fasting_stress, 11, 24)
