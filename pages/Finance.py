from json import load
import streamlit as st
import pandas as pd
import altair as alt
import datetime

from utils import find_file_id, download_file, load_gsheet, load_css

st.set_page_config(layout="wide")
load_css()

st.title('Finance')

@st.cache(ttl=60*60*24*2)
def load_cto_data():
    file_id = find_file_id("name contains 'CTO'")[0]['id']
    return load_gsheet(file_id, 'Transactions')

def load_dividends():
    dividends = load_cto_data()
    # Select relevant columns
    dividends = dividends[['Date', 'Type', 'Stock', 'Transacted Value']]
    # Keep dividends only
    dividends = dividends[dividends.Type == 'Div']
    # Parse date column
    # dividends['Date'] = pd.to_datetime(dividends.Date).dt.date
    dividends['Date'] = pd.to_datetime(dividends.Date)
    # Sort by date
    dividends = dividends.sort_values(by='Date', ascending=False)
    # Remove $ symbom and cast as float
    dividends['Transacted Value'] = dividends['Transacted Value'].str.strip('$').astype(float)
    # Keep rows until end of previous month
    # dividends = dividends[dividends.Date.dt.date < datetime.datetime.now().date().replace(day=1)]
    return dividends

dividends = load_dividends()

st.header('Dividends')

selected_scale = st.selectbox('Scale', options=['Yearly', 'Monthly'], index=0)
transformation = {'Yearly': 'year', 'Monthly': 'yearmonth'}[selected_scale]

dividends_chart = alt.Chart(dividends).mark_bar(color='#3B97F3').encode(
    x=alt.X(f'{transformation}(Date):O', title='Year'),
    y=alt.Y('sum(Transacted Value):Q', title=f'{selected_scale} amount', axis=alt.Axis(format='$.0f')),
    tooltip=[
        alt.Tooltip(f'{transformation}(Date):O', title='Date'),
        alt.Tooltip('sum(Transacted Value):Q', title='Dividends', format='$.0f'),
    ]
)

if selected_scale == 'Monthly':
    dividends_trend = alt.Chart(
        dividends.set_index('Date').resample('1M').sum().reset_index()
    ).mark_line(
        color='#F27716'
    ).transform_window(
        rolling_mean='mean(Transacted Value)',
        frame=[-11, 0] # 12 month average
    ).encode(
        x=alt.X(f'{transformation}(Date):O'),
        y=alt.Y('rolling_mean:Q', title=''),
    )

    st.altair_chart(dividends_chart + dividends_trend, use_container_width=True)

else:
    st.altair_chart(dividends_chart, use_container_width=True)

