import streamlit as st
import pandas as pd

st.set_page_config(
     page_title="Quantified Self",
    #  layout="wide",
    #  initial_sidebar_state="expanded",
     menu_items={
         'Get help': 'https://twitter.com/hugo_le_moine_',
         'Report a Bug': 'https://twitter.com/hugo_le_moine_',
         'About': "# Quantified Self. This is an app still under construction!"
     }
 )

st.title('Quantified Self')
st.markdown('This project aims at collecting, aggegating and reporting my personal data.')

st.markdown("""
    ### Data sources include:
    - <a href="/Anki" target="_self">AnkiDroid</a> : an app to learn vocabulary through flashcards.
    - Spotify : listening history.
    - Garmin : biometric data collected through my watch.
    - <a href="/Podcasts" target="_self">Podcast Addict</a> : a podcast player I use since 2017.
    - Zero : an intermittent fasting tracker.
    """,
    unsafe_allow_html=True
    )