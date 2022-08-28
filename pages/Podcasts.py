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
    thumbnails = pd.read_sql_query('SELECT _id, url FROM bitmaps', con).rename(columns={'_id': 'thumbnail_id'})
    podcasts = pd.read_sql_query('SELECT _id, name, thumbnail_id FROM podcasts', con)
    podcasts = pd.merge(
        left=podcasts,
        right=thumbnails,
        on='thumbnail_id'
    )
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
    # seen = seen[seen.playbackDate.dt.year >= 2018]
    seen['duration'] = seen.duration / pd.Timedelta('1 hour')
    podcast_df = pd.merge(
        left=podcasts.rename(columns={'name': 'podcast'}),
        right=seen,
        left_on='_id',
        right_on='podcast_id',
        how='right'
    )

    podcast_df = (podcast_df[['podcast', 'name', 'duration', 'playbackDate', 'url']]
                            .sort_values(by='playbackDate', ascending=False)
                )
    
    return podcast_df

def path_to_image_html(path):
    return '<img src="' + path + '" width="75" >'

@st.cache
def convert_images_df(input_df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return input_df.to_html(escape=False, formatters=dict(icon=path_to_image_html))

podcast_df = load_podcast_df()

st.title('PodcastAddict data')

st.subheader('Podcast listening Chart')
podcast_plot = alt.Chart(podcast_df).mark_bar().encode(
    x=alt.X('yearmonth(playbackDate):O', title='Month'),
    y=alt.Y('duration', aggregate='sum', title='Hours listened'),
    tooltip=alt.Tooltip('yearmonth(playbackDate)')
)
st.altair_chart(podcast_plot, use_container_width=True)

years = (podcast_df
    .playbackDate.dt.year
    .drop_duplicates()
    .sort_values(ascending=False)
    .astype(str)
    .tolist()
)

tabs = st.tabs(['All Time'] + years)

with tabs[0]:
    year_total, year_mean_duration, year_episodes, year_podcasts = st.columns(4)
    year_total.metric(
        label=f"Total listening",
        value=f'{podcast_df.duration.sum():.0f} hours',
    )
    year_mean_duration.metric(
        label=f"Mean episode duration",
        value=f'{podcast_df.duration.mean()*60:.0f} min',
    )
    year_episodes.metric(
        label=f"Number of episodes",
        value=f'{len(podcast_df)}',
    )
    year_podcasts.metric(
        label=f'Unique podcasts',
        value=podcast_df.podcast.nunique(),
    )

    st.subheader(f'All Time Top 10')
    year_top_10 = (podcast_df
        .groupby(by='podcast')
        .agg(
            total_hours=('duration', lambda x: round(sum(x))),
            n_episodes=('name', 'size'),
            min_per_episode=('duration', lambda x: round(x.mean()*60)),
            icon=('url', pd.Series.mode)
        )
        .sort_values(by='total_hours', ascending=False)
        .reset_index()
        [:10]
    )
    year_top_10.index += 1 
    year_top_10 = year_top_10[['icon', 'podcast', 'total_hours', 'n_episodes', 'min_per_episode']]

    st.markdown(
        convert_images_df(year_top_10),
        unsafe_allow_html=True
    )

for i, year in enumerate(years, 1):
    with tabs[i]:
        current_year = podcast_df[podcast_df.playbackDate.dt.year == int(year)]
        previous_year = podcast_df[podcast_df.playbackDate.dt.year == int(year) - 1]

        year_total, year_mean_duration, year_episodes, year_podcasts = st.columns(4)
        year_total.metric(
            label=f"{year} listening",
            value=f'{current_year.duration.sum():.0f} hours',
            delta=f"{current_year.duration.sum() - previous_year.duration.sum():.0f}h vs {int(year) - 1}"
        )
        year_mean_duration.metric(
            label=f"Mean episode duration",
            value=f'{current_year.duration.mean()*60:.0f} min',
            delta=f"{current_year.duration.mean()*60 - previous_year.duration.mean()*60:.0f} min vs {int(year) - 1}"
        )
        year_episodes.metric(
            label=f"Number of episodes",
            value=f'{len(current_year)}',
            delta=f"{len(current_year) - len(previous_year)} vs {int(year) - 1}"
        )
        year_podcasts.metric(
            label=f'Unique podcasts',
            value=current_year.podcast.nunique(),
            delta=f"{current_year.podcast.nunique() - previous_year.podcast.nunique()} vs {int(year) - 1}"
        )

        st.subheader(f'Top 10 of {year}')
        year_top_10 = (current_year
            .groupby(by='podcast')
            .agg(
                total_hours=('duration', lambda x: round(sum(x))),
                n_episodes=('name', 'size'),
                min_per_episode=('duration', lambda x: round(x.mean()*60)),
                icon=('url', pd.Series.mode)
            )
            .sort_values(by='total_hours', ascending=False)
            .reset_index()
            [:10]
        )
        year_top_10.index += 1 
        year_top_10 = year_top_10[['icon', 'podcast', 'total_hours', 'n_episodes', 'min_per_episode']]

        st.markdown(
            convert_images_df(year_top_10),
            unsafe_allow_html=True
        )
