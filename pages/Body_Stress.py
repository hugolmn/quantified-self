"""
Body stress page.
"""
import streamlit as st
import altair as alt
from utils import load_css, get_garmin_data
st.set_page_config(layout="wide")
load_css()

st.title('Body Stress')

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
        # legend=(alt.Legend(orient='none'))
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
        color='white',
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

stress_df_history_chart = alt.Chart(stress_df_history).mark_area(opacity=0.85, interpolate='step').encode(
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
    use_container_width=True,
    theme='streamlit'
)
