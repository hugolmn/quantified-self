import streamlit as st

st.set_page_config(
    page_title="Quantified Self",
    #  layout="wide",
    #  initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://twitter.com/hugo_le_moine_",
        "Report a Bug": "https://twitter.com/hugo_le_moine_",
        "About": "# Quantified Self. Personal data collection and reporting.",
    },
)

st.title("Quantified Self")
st.markdown("This project aims at collecting, storing and reporting my personal data.")

st.markdown(
    """
    ### Available pages:
    - <a href="/Activity" target="_self">Activity</a>: steps history.
    - <a href="/Anki" target="_self">Anki</a>: AnkiDroid revision history.
    - <a href="/Body_Stress" target="_self">Body Stress</a>: Stress level from Garmin.
    - <a href="/Carbon_Footprint" target="_self">Carbon Footprint</a>: CO2 emissions from transportation.
    - <a href="/Fasting" target="_self">Fasting</a>: fasting history and analysis.
    - <a href="/Finance" target="_self">Finance</a>: dividends collected.
    - <a href="/Heart_Rate" target="_self">Heart Rate</a>: resting heart rate.
    - <a href="/Podcasts" target="_self">Podcasts</a>: podcast listening history and yearly tops.
    - <a href="/Sleep" target="_self">Sleep</a>: Sleep data from Garmin.
    - <a href="/Weight" target="_self">Weight</a>: Weight data from Garmin.
    """,  # noqa: E501
    unsafe_allow_html=True,
)

st.markdown(
    """
    ### Data sources include:
    - AnkiDroid: an app to learn vocabulary through flashcards.
    - Garmin: biometric data collected through my watch.
    - Google Sheets: manual collection of plane and train rides.
    - My Stock Portfolio: android app to track investments.
    - Podcast Addict: a podcast player I use since 2017.
    - Spotify: listening history.
    - Zero : an intermittent fasting tracker.
    """,
    unsafe_allow_html=True,
)
