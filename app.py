import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Wimbledon Draft Tracker", layout="wide")

# -----------------------
# PLAYER → MANAGER MAP
# -----------------------
mapping = {
    "Taylor Fritz": "Villani",
    "Daniil Medvedev": "Jesse",
    "Andrey Rublev": "Sam",
    "Casper Ruud": "Schur",
    "Felix Auger-Aliassime": "Will",
    "Ben Shelton": "Hunter",
    "Novak Djokovic": "Shanfeldt",
    "Alexander Zverev": "Dylan",
    "Flavio Cobolli": "Shahar",
    "Alex de Minaur": "Schneider",
    "Jannik Sinner": "Kevin",
    "Alexander Bublik": "Eran"
}

# -----------------------
# FETCH LIVE DATA (NO KEY)
# -----------------------
@st.cache_data(ttl=60)
def fetch_data():
    try:
        url = "https://sportscore.com/api/widget/matches?sport=tennis"
        res = requests.get(url)
        return res.json().get("matches", [])
    except:
        return []

# -----------------------
# PARSE DATA
# -----------------------
def parse_data(matches):
    players = {}

    for match in matches:
