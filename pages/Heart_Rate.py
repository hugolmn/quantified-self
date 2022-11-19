"""
Heart rate page.
"""
import streamlit as st
import altair as alt
import numpy as np
import seaborn as sns
from utils import load_css, get_garmin_data
alt.themes.enable("streamlit")
st.set_page_config(layout="wide")
load_css()

st.title('Heart Rate')

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
    x=alt.Y(
        'yearmonthdate(date):T',
        title='',
        axis=alt.Axis(
            format='%B %Y',
            tickCount='month',
            grid=True
        )
    ),
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

rhr_df['Weekly Mean'] = rhr_df.resting_heart_rate.rolling(7, min_periods=0, center=True).mean()
rhr_df['Monthly Mean'] = rhr_df.resting_heart_rate.rolling(30, min_periods=0, center=True).mean()

rolling_mean_chart = alt.Chart(
    rhr_df.drop(columns='resting_heart_rate')
          .melt('date', var_name='rolling', value_name='resting_heart_rate')
).mark_line(color='#3B97F3').encode(
    x=alt.X('date', title=''),
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
    x=alt.X(
        'resting_heart_rate:N',
        title=''
        # title='Resting Heart Rate',
    ),
    y=alt.Y('count()', title='Count')
)
col2.altair_chart(rhr_histogram, use_container_width=True)

# st.header('Heart Rate')
# hr_df = get_garmin_data("""SELECT date, hr FROM heart_rate WHERE hr > 0""").copy()

# st.altair_chart(
#     alt.Chart(
#         hr_df.groupby(hr_df.date.dt.date)
#              .hr
#              .quantile(q=np.arange(0, 1.05, .05))
#              .reset_index()
#     ).mark_line().encode(
#         x='date:T',
#         y='hr:Q',
#         color='level_1'
#     )
# )

# percentile_hr = hr_df.groupby(hr_df.date.dt.date).hr.quantile(q=np.arange(0, 1.1, .1)).unstack()
# percentile_hr.columns = [f"{decile*100:.0f}-{decile*100+10:.0f}%" for decile in percentile_hr.columns]

# percentile_hr = percentile_hr.reset_index()
# palette = sns.color_palette("vlag", 10).as_hex()
# scale = alt.Scale(domain=percentile_hr.columns[1:-1].tolist(), range=palette)

# # Create layers for chart
# def make_layer(percentile_hr, col1, col2):
#     return alt.Chart(percentile_hr.assign(color=col1)).mark_area().encode(
#         x=alt.X('date:T', title='', axis=alt.Axis(format='%Y')),
#     ).encode(
#         y=alt.Y(
#             f"{col1}:Q",
#             title='Stock Price',
#             axis=alt.Axis(format='.0f'),
#             scale=alt.Scale(zero=False)
#         ),
#         y2=alt.Y2(
#             f"{col2}:Q",
#             title='Stock Price'
#         ),
#         color=alt.Color(
#             f"color:N",
#             # title=f"""{ticker} {period} Yield Percentile. Current Yield: {
#             #     df.iloc[-1].DividendYield:.2%} (Top {
#             #     1 - df.DividendYield.rank(pct=True).iloc[-1]:.0%})""",
#             scale=scale,
#             legend=alt.Legend(
#                 orient='top',
#                 titleFontSize=30,
#                 labelFontSize=20,
#                 titleLimit=0
#             )
#         ),
#         opacity=alt.value(0.8)
#     )

# layers=[]
# for col1, col2 in zip(percentile_hr.columns[1:-1], percentile_hr.columns[2:]):
#     layers.append(make_layer(percentile_hr, col1, col2))

# chart = alt.layer(
#     *layers
# ).properties(
#     width=1200,
#     height=675
# ).configure(
#     font='Lato'
# ).configure_axisY(
#     labelFontSize=25,
#     titleFontSize=20
# ).configure_axisX(
#     labelAngle=-45,
#     labelFontSize=25
# )

# st.altair_chart(chart)