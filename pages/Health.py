"""
Health page:
- Resting Heart Rate (RHR) data
- Stress data
- Calories
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
).interactive()

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

# Stress charts
st.header('Stress')

selected_period = st.selectbox('Period', options=['Week', 'Month', 'Year', 'All Time'], index=2)
n_days = {'Week': 7, 'Month': 30, 'Year': 365, 'All Time': 365*100}[selected_period]

stress_df = get_garmin_data(
    """
    SELECT 
        date,
        rest_stress_duration,
        low_stress_duration,
        medium_stress_duration,
        high_stress_duration
    FROM stats
    ORDER BY date ASC
    """
)

average_stress = get_garmin_data(
    """
    SELECT date, average_stress_level FROM stats
    ORDER BY date ASC
    """
)

stress_df.columns = stress_df.columns.str.split('_').str[0]

stress_df_period = (stress_df
    [['rest', 'low', 'medium', 'high']]
    .iloc[-n_days:]
    .mean()
    .to_frame('duration')
    .reset_index()
)
stress_df_period['duration'] = stress_df_period.duration.div(stress_df_period.duration.sum())
stress_df_period['order'] = stress_df_period.index

col1, col2 = st.columns(2)

stress_donut = alt.Chart(stress_df_period).mark_arc(innerRadius=100).encode(
    theta=alt.Theta('duration:Q'),
    color=alt.Color(
        'index:N',
        title='Stress level',
        scale=alt.Scale(
            domain=['rest', 'low', 'medium', 'high'],
            range=['#3B97F3', '#FFB154', '#F27716', '#DE5809'],
        ),
        legend=(alt.Legend(orient='none'))
    ),
    order=alt.Order('order', sort='descending'),
    tooltip=[
        alt.Tooltip('index', title='Stress level'),
        alt.Tooltip('duration', title='Duration', format='.0%')
    ]
).properties(
    title=alt.TitleParams(
        selected_period,
        subtitle=f'{average_stress.average_stress_level.iloc[-n_days:].mean():.0f}',
        subtitleFontSize=50,
        align='center',
        dy=200
    ),
)

col1.altair_chart(stress_donut, use_container_width=True)

stress_df_history = (stress_df
    .iloc[-n_days:]
    .melt(
        'date',
        var_name='stress_level',
        value_name='duration'
    )
)
stress_df_history['duration'] = (stress_df_history
    ['duration']
    .div(stress_df_history.groupby('date')['duration'].transform(sum))
)

stress_df_history_chart = alt.Chart(stress_df_history).mark_area(opacity=0.85).encode(
    x=alt.X('date:T'),
    y=alt.Y(
        'duration:Q',
        title='Percentage of day',
        stack='normalize',
        axis=alt.Axis(format='%')
    ),
    color=alt.Color(
        'stress_level:N',
        title='Stress level',
        scale=alt.Scale(
            domain=['rest', 'low', 'medium', 'high'],
            range=['#3B97F3', '#FFB154', '#F27716', '#DE5809'],
            reverse=False
        ),
        legend=None
    ),
    order=alt.Order(),
    tooltip=[
        alt.Tooltip('date:T', title='Date'),
        alt.Tooltip('stress_level:N', title='Stress level'),
        alt.Tooltip('duration:Q', title='Duration', format='.0%')
    ]
)

average_stress_plot = alt.Chart(
    average_stress.iloc[-n_days:].assign(legend='Weekly')
).mark_line(
    color=st.secrets["theme"]['primaryColor']
).transform_window(
    rolling_mean='mean(average_stress_level)',
    frame=[-7, 0]
).encode(
    x=alt.X('date'),
    y=alt.Y('rolling_mean:Q',
        title='Average Stress Level',
        scale=alt.Scale(
            domain=(0, 100),
        )
    ),
    color=alt.Color(
        'legend',
        title='Rolling Mean',
        scale=alt.Scale(
            range=['#FFFFFF', '#FFFFFF'],
        ),
        legend=alt.Legend(orient='bottom-left')
    )
)

col2.altair_chart(
    (
        alt.layer(stress_df_history_chart, average_stress_plot)
           .resolve_scale(y='independent', color='independent')
    ),
    use_container_width=True
)

# Calories charts
st.header('Calories')

calories_df = get_garmin_data("""SELECT date, active_kilocalories, bmr_kilocalories FROM stats""")
calories_df = calories_df.melt(
    'date',
    var_name='Type',
    value_name='calories',
)

# col1, col2 = st.columns(2)

calories_plot = alt.Chart(calories_df).mark_bar().encode(
    x=alt.X('yearmonthdate(date):O', title='Date'),
    y=alt.Y('sum(calories):Q', scale=alt.Scale(domainMin=1500, clamp=True)),
    color=alt.Color('Type', scale=alt.Scale(range=['#F27716', '#3B97F3'])),
    tooltip=[
        alt.Tooltip('yearmonthdate(date):O', title="Date"),
        alt.Tooltip('Type:N'),
        alt.Tooltip('calories', title="Calories"),
    ]
).interactive()
st.altair_chart(calories_plot, use_container_width=True)
