"""
Weight page.
"""
import streamlit as st
import altair as alt
import numpy as np
import seaborn as sns
from utils import load_css, get_garmin_data
st.set_page_config(layout="wide")
load_css()

st.title('Weight')

# Get Weight data
weight_df = get_garmin_data("""SELECT date, weight FROM weight""").copy()

# Display points
weight_points = alt.Chart(weight_df).mark_point(color='#FFFFFF').encode(
    x=alt.X(
        'date:T',
        title='',
        axis=alt.Axis(
            format='%Y',
            tickCount='year',
            grid=True
        )
    ),
    y=alt.Y(
        'weight',
        title='Weight',
        scale=alt.Scale(zero=False)
    )
)
# Display line
weight_chart = alt.Chart(weight_df).mark_line(color=st.secrets["theme"]['primaryColor'], interpolate='basis').encode(
    x=alt.X('date:T', title=''),
    y=alt.Y('weight', axis=alt.Axis(format=''),scale=alt.Scale(zero=False))
)

# Display chart in streamlit
st.altair_chart(
    weight_points + weight_chart,
    use_container_width=True,
    theme='streamlit'
)
