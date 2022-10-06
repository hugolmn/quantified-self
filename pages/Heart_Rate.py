"""
Heart rate page.
"""
import streamlit as st
import altair as alt
from utils import load_css, get_garmin_data

st.set_page_config(layout="wide")
load_css()

st.title('Health')

# Resting heart rate charts
st.header(f'Resting Heart Rate (RHR)')
# Get RHR data
rhr_df = get_garmin_data("""SELECT date, resting_heart_rate FROM stats""").copy()
st.write(f'{len(rhr_df)} days of data collected. RHR is calculated using the lowest 30 minute average in a 24 hour period.')

# Calculate metrics: weekly, monthly, quarterly and all time RHR mean.
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
    delta_color='inverse',
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

# RHR plots: history and histogram
col1, col2 = st.columns(2)

# Scatterplot + weekly and monthly rolling means
rhr_scatterplot = alt.Chart(rhr_df).mark_point(color='#FFFFFF').encode(
    x=alt.Y('yearmonthdate(date):T', title='Date'),
    y=alt.Y(
        'resting_heart_rate:Q',
        title='Resting Heart Rate',
        scale=alt.Scale(zero=False)
    ),
    tooltip=[
        alt.Tooltip('date', title='Date'),
        alt.Tooltip('resting_heart_rate', title='RHR')
    ]
).interactive(bind_y=False)

rhr_df['Weekly Mean'] = rhr_df.resting_heart_rate.rolling(7, min_periods=0, center=False).mean()
rhr_df['Monthly Mean'] = rhr_df.resting_heart_rate.rolling(30, min_periods=0, center=False).mean()

rolling_mean_chart = alt.Chart(
    rhr_df.drop(columns='resting_heart_rate')
          .melt('date', var_name='rolling', value_name='resting_heart_rate')
).mark_line(color='#3B97F3').encode(
    x=alt.X('date', title='Date'),
    y=alt.Y('resting_heart_rate'),
    color=alt.Color(
        'rolling:N',
        title='',
        scale=alt.Scale(
            range=[
                st.secrets["theme"]['primaryColor'],
                st.secrets["theme"]['secondaryColor']
            ]
        ),
        legend=alt.Legend(
            orient='bottom-left',
        )
    ),
)
col1.altair_chart(rhr_scatterplot + rolling_mean_chart, use_container_width=True)

# Density plot
rhr_histogram = alt.Chart(rhr_df).mark_bar(color='#3B97F3').encode(
    x=alt.X('resting_heart_rate:N', title='Resting Heart Rate'),
    y=alt.Y('count()', title='Count')
)
col2.altair_chart(rhr_histogram, use_container_width=True)

