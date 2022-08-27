from json import load
import streamlit as st
import pandas as pd
import sqlite3
import os
import zipfile
import altair as alt

from utils import download_file, find_file_id

@st.cache(ttl=60*60*24*2)
def load_podcast_addict_archive():
    file_id = find_file_id("name contains 'PodcastAddict_autoBackup'")[0]['id']
    file = download_file(file_id=file_id)
    podcast_addict_archive = zipfile.ZipFile(file)
    podcast_addict_archive.extract('podcastAddict.db', path='data')

def sqlite_podcast_addict():
    load_podcast_addict_archive()
    con = sqlite3.connect(os.path.join('data', 'podcastAddict.db'))
    return con

def load_podcast_df():
    con = sqlite_podcast_addict()
    podcasts = pd.read_sql_query('SELECT _id, name FROM podcasts', con)
    seen = pd.read_sql_query(
        '''SELECT podcast_id, name, duration, playbackDate
        FROM episodes 
        WHERE seen_status == 1 
                AND duration != -1
                AND playbackDate != -1
        ''',
        con
    )

    seen['playbackDate'] = pd.to_datetime(seen.playbackDate, unit='ms')
    seen.loc[seen.duration.apply(len) == 5, 'duration'] = '00:' + seen.loc[seen.duration.apply(len) == 5, 'duration']
    seen['duration']= pd.to_timedelta(seen.duration)
    seen = seen[seen.playbackDate.dt.year >= 2018]
    seen['duration'] = seen.duration / pd.Timedelta('1 hour')
    podcast_df = pd.merge(
        left=podcasts.rename(columns={'name': 'podcast'}),
        right=seen,
        left_on='_id',
        right_on='podcast_id',
        how='right'
    )

    podcast_df = (podcast_df[['podcast', 'name', 'duration', 'playbackDate']]
                            .sort_values(by='playbackDate', ascending=False)
                )
    
    return podcast_df


podcast_df = load_podcast_df()

# total, episodes, podcasts = st.columns(3)
# total.metric(label='Total listening', value=f'{int(df_podcasts.duration.sum())} hours')
# episodes.metric(label='#Episodes', value=len(df_podcasts))
# podcasts.metric(label='#Podcasts', value=df_podcasts.podcast.nunique())

st.title('Podcast listening Chart')
podcast_plot = alt.Chart(podcast_df).mark_bar().encode(
    y=alt.Y('duration', aggregate='sum'),
    x='yearmonth(playbackDate):O',
    tooltip=[]
)
st.altair_chart(podcast_plot, use_container_width=True)

years = (podcast_df
    .playbackDate.dt.year
    .drop_duplicates()
    .sort_values(ascending=False)
    .astype(str)
    .tolist()
)

tabs = st.tabs(years)
for i, year in enumerate(years):
    with tabs[i]:
        current_year_total = (podcast_df[podcast_df.playbackDate.dt.year == int(year)]
                                .duration
                                .sum()
                                .astype(int)
        )
        previous_year_total = (podcast_df[podcast_df.playbackDate.dt.year == int(year) - 1]
                                .duration
                                .sum()
                                .astype(int)
        
        )
        st.metric(
            label=f"{year} Total",
            value=f"{current_year_total} hours",
            delta=f"{current_year_total - previous_year_total}h vs {int(year) - 1}")
            
        st.subheader(f'Yearly top 10')
        st.table(podcast_df
            [podcast_df.playbackDate.dt.year == int(year)]
            .groupby(by='podcast')
            .duration
            .sum()
            .sort_values(ascending=False)
            .astype(int)
            .reset_index()
            [:10]
        )
