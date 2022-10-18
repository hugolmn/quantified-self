import os
import pandas as pd
import streamlit as st
import altair as alt
import sqlite3
from utils import find_file_id, download_file, load_css
alt.themes.enable("streamlit")
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
hsk_df = pd.merge(left=hsk_df, right=hsk_revlog, on='cid')

# Display metrics



history_plot = alt.Chart(hsk_df[['id']]).mark_bar(color=st.secrets["theme"]['primaryColor']).encode(
    x='yearmonthdate(id):T',
    y='count():Q'
)
st.altair_chart(history_plot, use_container_width=True)

cumulative_hsk = hsk_df.drop_duplicates(subset=['cid'])
cumulative_hsk = cumulative_hsk.assign(cumcount=cumulative_hsk.sort_values(by='id').groupby('HSK').cumcount())

hsk_plot = alt.Chart(cumulative_hsk[:1000]).mark_line().encode(
    x='id:T',
    y='cumcount:Q',
    color='HSK'
)
st.altair_chart(hsk_plot, use_container_width=True)