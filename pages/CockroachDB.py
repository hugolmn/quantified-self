import os
import streamlit as st
os.system(f"curl --create-dirs -o $HOME/.postgresql/root.crt -O {st.secrets['get_certificate_cockroachdb']}")