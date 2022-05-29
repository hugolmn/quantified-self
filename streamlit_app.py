import streamlit as st
import pandas as pd

st.title("Google Fit data analysis")

df = pd.DataFrame()

uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True)
if uploaded_files:
     df = pd.concat([
         pd.read_csv(file).assign(start_date=file.name.split('.')[0])
         for file in uploaded_files
     ]) 
     st.dataframe(df)
