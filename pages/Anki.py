import os
import pandas as pd
import streamlit as st
import altair as alt
import sqlite3
from utils import find_file_id, download_file, load_css
st.set_page_config(layout="wide")
load_css()

@st.cache(ttl=60*60*12)
def get_anki_db():
    file_id = find_file_id("name contains 'collection.anki2'")[0]['id']
    file = download_file(file_id=file_id)
    return file

def load_anki():
    anki_db = get_anki_db()
    with open(os.path.join('data', 'anki.db'), 'wb') as anki_file:
        anki_file.write(anki_db.getbuffer())

    con = sqlite3.connect(os.path.join('data', 'anki.db'))
    return con

anki_con = load_anki()

st.title('Anki')

# Loading cards
cards = pd.read_sql('SELECT * FROM cards', anki_con)
# Loading notes
notes = pd.read_sql('SELECT * FROM notes', anki_con)
# Loading revlog
revlog = pd.read_sql('SELECT * FROM revlog', anki_con)
revlog['id'] = pd.to_datetime(revlog.id, unit='ms', utc=True).dt.tz_convert('Europe/Paris')
# Loading decks
decks = pd.read_json(pd.read_sql('SELECT * FROM col', anki_con).decks[0]).T
# Get HSK data
hsk_deck_id = decks[decks.name.str.contains('HSK')].id.iloc[0]
hsk_cards = cards[cards.did == hsk_deck_id].rename(columns={'id': 'cid'})
hsk_notes = notes[notes.id.isin(hsk_cards.nid)].rename(columns={'id': 'nid'})
hsk_notes = hsk_notes.assign(HSK=hsk_notes.tags.str.extract('(HSK\d)'))
hsk_notes = hsk_notes.drop(columns=['tags'])
hsk_revlog = revlog[revlog.cid.isin(hsk_cards.cid)]

hsk_df = pd.merge(left=hsk_cards, right=hsk_notes, on='nid')
hsk_detailed_revlog = pd.merge(left=hsk_df, right=hsk_revlog, on='cid')

# Info about Anki
st.write("Anki is an app I use every day to learn chinese vocabulary.")
st.header('Overall metrics')
overall_metrics = st.columns(3)
overall_metrics[0].metric(
    label='Cards reviewed',
    value=len(hsk_detailed_revlog)
)
overall_metrics[1].metric(
    label='Current streak',
    value=f"{hsk_detailed_revlog['id'].dt.date.nunique():.0f} days"
)

total_time_spent = hsk_detailed_revlog['time'].astype(int).sum() // 1000
overall_metrics[2].metric(
    label='Total time spent',
    value=f"{total_time_spent // 3600:.0f}h {(total_time_spent // 60) % 60:.0f}min"
)

st.header('HSK progress')
hsk_metrics = st.columns(6)
for i, hsk_level in enumerate(hsk_df.HSK.dropna().unique()):
    hsk_df_ = hsk_df[hsk_df.HSK == hsk_level]
    hsk_metrics[i].metric(
        label=hsk_level,
        value=f"{len(hsk_df_[hsk_df_.ivl == 200]) / len(hsk_df_):.0%}"
    )

# hsk_chart_levels = alt.Chart(
#     hsk_df.dropna(subset=['HSK'])
# ).transform_density(
#     'ivl',
#     groupby=['HSK'],
#     as_=['ivl', 'density'],
#     extent=[1, 200],
# ).mark_area().encode(
#     x=alt.X('ivl:Q'),
#     y=alt.Y('density:Q')
# ).facet(
#     # row=alt.Row('HSK')
#     "HSK",
#     columns=6
# )

# st.altair_chart(hsk_chart_levels, theme='streamlit')

# Display metrics
# Day changes at 3am
history_plot = alt.Chart(
    hsk_detailed_revlog[['id']] - pd.Timedelta('3H')
).mark_bar(
    color=st.secrets["theme"]['primaryColor']
).encode(
    x=alt.X('yearmonthdate(id):T', title='', axis=alt.Axis(format='%Y', tickCount='year', grid=True)),
    y=alt.Y('count():Q', title='Cards Reviewed')
)
st.altair_chart(history_plot, use_container_width=True, theme='streamlit')

cumulative_hsk = hsk_detailed_revlog.drop_duplicates(subset=['cid'])
cumulative_hsk = cumulative_hsk.dropna(subset=['HSK'])
cumulative_hsk = cumulative_hsk.assign(
    cumcount=(cumulative_hsk
        .sort_values(by='id')
        .groupby('HSK')
        .cumcount()
    )
)

hsk_plot = alt.Chart(cumulative_hsk).mark_line().encode(
    x='id:T',
    y='cumcount:Q',
    color='HSK'
)
st.altair_chart(hsk_plot, use_container_width=True, theme='streamlit')