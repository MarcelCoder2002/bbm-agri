"""
Application Streamlit avec authentification et base de données
Structure modulaire avec streamlit-authenticator
"""
import streamlit as st

# Import des modules locaux
from config.settings import APP_CONFIG
from modules.app import App

# Configuration de la page
st.set_page_config(**APP_CONFIG)

if __name__ == '__main__':
	App.run()
