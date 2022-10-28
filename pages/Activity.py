import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime

from utils import load_css, get_garmin_data
alt.themes.enable("streamlit")
st.set_page_config(layout="wide")
load_css()

def get_steps_detailed_data():
    df = get_garmin_data("""SELECT * FROM steps""")
    df = df.assign(date=pd.to_datetime(df.date, utc=True).dt.tz_convert('Europe/Paris'))
    df['day_of_week'] = np.where(df.date.dt.weekday >= 6, 'weekend', 'weekday')
    return df
    
st.title('Activity')

st.header(f'Steps')
steps_df = get_steps_detailed_data().copy()

def generate_metric_steps(col, label, df, days=None):
    if days:
        steps = df[df.date > df.date.max() - pd.Timedelta(f'{days}D')].steps.sum() / days
    else:
        steps = df.steps.sum() / df.date.dt.date.nunique()

    return col.metric(
        label,
        f"{steps/1000:.1f}K",
        delta=f"{(steps-df.steps.sum() / df.date.dt.date.nunique())/1000:.1f}k vs all time" if days is not None else None
    )

steps_metrics = {
    'Week': 7,
    'Month': 30,
    'Year': 365,
    'All Time': None
}
for params, col in zip(steps_metrics.items(), st.columns(4)):
    generate_metric_steps(col, params[0], steps_df, params[1])

# Steps plots
col1, col2 = st.columns(2)

# 7 day rolling average + scatterplot
daily_steps = (steps_df
    .groupby(steps_df['date'].dt.date, group_keys=False)
    .sum()
    .reset_index()
)
daily_steps['date'] = pd.to_datetime(daily_steps.date)

steps_scatterplot_daily = alt.Chart(daily_steps).mark_bar(
    color=st.secrets["theme"]['primaryColor'],
    clip=True
).encode(
    x=alt.X(
        'yearmonthdate(date):T',
        title='Date',
        # scale=alt.Scale(
        #     domain=[
        #         daily_steps['date'].iloc[-90].isoformat(),
        #         daily_steps['date'].iloc[-1].isoformat(),
        #     ]
        # )
    ),
    y=alt.Y(
        'steps:Q',
        title='Daily Steps',
    ),
    tooltip=['date', 'steps']
).interactive(bind_y=False)

steps_weekly_rolling_mean_plot = alt.Chart(
    daily_steps.assign(legend='30-day average')
).mark_line(
    color=st.secrets["theme"]['secondaryColor']
).transform_window(
    rolling_mean='mean(steps)',
    frame=[-15, -15]
).encode(
    x=alt.X('yearmonthdate(date):T'),
    y=alt.Y('rolling_mean:Q', title=''),
    color=alt.Color(
        'legend',
        title='',
        scale=alt.Scale(
            range=[st.secrets["theme"]['secondaryColor']]*2
        ),
        legend=alt.Legend(orient='top-right')
    )
)

col1.altair_chart(
    steps_scatterplot_daily + steps_weekly_rolling_mean_plot,
    use_container_width=True
)

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
)
col2.altair_chart(steps_scatterplot_hourly, use_container_width=True)


st.header(f'Activity Level')

col1, col2 = st.columns(2)

activity_level_chart = alt.Chart(steps_df.dropna(subset=['activity_level'])).mark_bar().encode(
    x=alt.X('yearmonthdate(date)', title='Date'),
    y=alt.Y('count(activity_level)', stack='normalize', title='Percentageof day'),
    color=alt.Color('activity_level:N', title='Activity level'),
    tooltip=[
        alt.Tooltip('yearmonthdate(date)', title='Date'),
        alt.Tooltip('activity_level', title='Activity level'),
    ]
)

col1.altair_chart(activity_level_chart, use_container_width=True)


sedentarity_chart = alt.Chart(steps_df[steps_df.activity_level.isin(['active', 'highlyActive'])]).mark_bar().encode(
    x=alt.X('yearmonthdate(date)', title='Date'),
    y=alt.Y('count(activity_level)', title='Percentageof day'),
    color=alt.Color('activity_level:N', title='Activity level'),
    tooltip=[
        alt.Tooltip('yearmonthdate(date)', title='Date'),
        alt.Tooltip('activity_level', title='Activity level'),
    ]
)
col2.altair_chart(sedentarity_chart, use_container_width=True)
