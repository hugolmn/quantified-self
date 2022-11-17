import io
import streamlit as st
import pandas as pd
import altair as alt
import datetime

from utils import find_file_id, download_file, load_gsheet, load_css
alt.themes.enable("streamlit")
st.set_page_config(layout="wide")
load_css()

st.title('Finance')

@st.cache(ttl=60*60*24*7)
def load_dividend_data():
    file_id = find_file_id("name contains 'MSP'")[0]['id']
    csv = download_file(file_id)

    df = pd.read_csv(
        io.StringIO(
            csv.getvalue().decode('utf-8')
        )
    )

    df = df.dropna(subset=['Transaction Date'])
    df = df[df.Type == 'Dividend']
    df = df[(df.Portfolio == 'CTO') | (df.Portfolio == 'ETF')]

    df['Date'] = pd.to_datetime(df['Transaction Date'].str.split().str[0])
    df['Dividends'] = df['Shares Owned']

    df = df[['Symbol', 'Name', 'Date', 'Dividends', 'Portfolio']]

    df = df[df.Date.dt.date < datetime.datetime.now().date().replace(day=1)]
    df = df.sort_values(by='Date')
    return df

st.header('Dividends')
dividends = load_dividend_data()

selected_scale = st.selectbox('Scale', options=['Yearly', 'Monthly'], index=1)
transformation = {'Yearly': 'year', 'Monthly': 'yearmonth'}[selected_scale]

dividends_chart = alt.Chart(dividends).mark_bar(color='#3B97F3').encode(
    x=alt.X(
        f'{transformation}(Date):O',
        title='Year'
    ),
    y=alt.Y(
        'sum(Dividends):Q',
        title=f'{selected_scale} dividends',
        axis=alt.Axis(format='$.0f')
    ),
    tooltip=[
        alt.Tooltip(f'{transformation}(Date):O', title='Date'),
        alt.Tooltip('sum(Dividends):Q', title='Dividends', format='$.0f'),
        alt.Tooltip('Portfolio')
    ],
    color=alt.Color(
        'Portfolio',
        sort='descending',
        scale=alt.Scale(
            domain=[
                'CTO',
                'ETF',
            ],
            range=[
                st.secrets["theme"]['primaryColor'],
                st.secrets["theme"]['secondaryColor']
            ]
        )
    ),
    order=alt.Order('Portfolio')
)

if selected_scale == 'Monthly':
    dividends_trend = alt.Chart(
        dividends.set_index('Date').resample('1M').sum().reset_index()
    ).mark_line(
        color='#FFFFFF'
    ).transform_window(
        rolling_mean='sum(Dividends)',
        frame=[-11, 0] # 12 month average
    ).encode(
        x=alt.X(f'{transformation}(Date):O', title='Year'),
        y=alt.Y(
            'rolling_mean:Q',
            title=f'TTM dividends',
            axis=alt.Axis(format='$.0f', grid=True)
        ),
    )
    st.altair_chart(
        alt.layer(
            dividends_chart,
            dividends_trend
        ).resolve_scale(y='independent'),
        use_container_width=True
    )

else:
    st.altair_chart(dividends_chart, use_container_width=True)

years = (dividends
    .Date
    .dt.year
    .sort_values(ascending=False)
    .unique()
    .astype(str)
    .tolist()
)

tabs = st.tabs(['All Time'] + years)

with tabs[0]:

    pt = (dividends
        .assign(Year=dividends.Date.dt.year) # Get year
        .pivot_table(
            index='Symbol',
            columns='Year',
            values=['Dividends'],
            aggfunc='sum',
            margins=True
        )
        .iloc[:-1] # Drop "All" row
        .droplevel(0, axis=1) # Drop multiIndex column
        .sort_values(by='All', ascending=False) # Sort by All time dividends
        .iloc[:20] # Keep 20 top rows
        .drop(columns=['All']) # Drop "All" column
        .stack() # Stack years
        .to_frame('Dividends') # Convert to a single column dataframe
        .reset_index()
    )

    dividends_per_stock = alt.Chart(pt).mark_bar(color='#3B97F3').encode(
        x=alt.X('sum(Dividends)', title='Dividends', axis=alt.Axis(format='$.0f')),
        y=alt.Y('Symbol:N', sort='-x'),
        color=alt.Color(
            'Year:N',
            title='Year',
            sort='descending',
            scale=alt.Scale(scheme='darkblue', reverse=False),
            legend=alt.Legend(orient='top')
        ),
        order=alt.Order(
            'Year',
            sort='descending'
        )
    ).properties(
        title='Top 20 of All Time'
    ).configure_title(
        fontSize=25,
        font='Lato'
    )

    st.altair_chart(dividends_per_stock, use_container_width=True)

for i, year in enumerate(years, 1):
    with tabs[i]:
        dividends_ = (dividends
            [dividends.Date.dt.year == int(year)]
            .groupby('Symbol')
            .Dividends.sum()
            .sort_values(ascending=False)
            .iloc[:10]
            .reset_index()
        )

        dividends_per_stock = alt.Chart(
            dividends_
        ).mark_bar(color='#3B97F3').encode(
            x=alt.X(
                'sum(Dividends)',
                title='Dividends',
                axis=alt.Axis(format='$.0f', tickMinStep=1)
            ),
            y=alt.Y('Symbol:N', sort='-x'),
        ).properties(
            title=f'Top 10 of {year}'
        ).configure_title(
            fontSize=25,
            font='Lato'
        )

        st.altair_chart(dividends_per_stock, use_container_width=True)
