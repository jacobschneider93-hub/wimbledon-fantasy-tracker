import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Wimbledon Draft Tracker", layout="wide")

# -----------------------
# CONFIG
# -----------------------
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://sportbex-tennis.p.rapidapi.com/live"  # example RapidAPI endpoint

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "sportbex-tennis.p.rapidapi.com"
}

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
# FETCH LIVE DATA
# -----------------------
@st.cache_data(ttl=60)
def fetch_live_data():
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        return response.json()
    except Exception as e:
        st.warning("Live API unavailable — showing last known data.")
        return []

# -----------------------
# PARSE LIVE DATA
# -----------------------
def parse_data(api_data):
    players = {}

    for match in api_data:
        for p in match.get("players", []):
            name = p.get("name")

            if name not in mapping:
                continue

            if name not in players:
                players[name] = {
                    "Matches Won": 0,
                    "Sets Won": 0,
                    "Aces": 0,
                    "Games Won": 0,
                    "Seed": p.get("seed", 999)
                }

        # Winner
        winner = match.get("winner")

        if winner in players:
            players[winner]["Matches Won"] += 1

        # Stats
        for p in match.get("players", []):
            name = p.get("name")
            if name not in players:
                continue

            players[name]["Sets Won"] += p.get("sets_won", 0)
            players[name]["Aces"] += p.get("aces", 0)
            players[name]["Games Won"] += p.get("games_won", 0)

    return players

# -----------------------
# BUILD TABLE
# -----------------------
def build_df(players):
    rows = []
    for player, stats in players.items():
        rows.append({
            "Player": player,
            "Manager": mapping[player],
            **stats
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.sort_values(
        by=["Matches Won", "Sets Won", "Aces", "Games Won", "Seed"],
        ascending=[False, False, False, False, True]
    )

    df["Rank"] = range(1, len(df) + 1)
    return df

# -----------------------
# CLINCH LOGIC
# -----------------------
def add_clinch(df):
    df["Clinched"] = False

    if len(df) < 2:
        return df

    for i in range(len(df) - 1):
        lead = df.iloc[i]["Matches Won"] - df.iloc[i+1]["Matches Won"]
        if lead >= 2:
            df.at[df.index[i], "Clinched"] = True

    return df

# -----------------------
# UI
# -----------------------
st.title("🏆 Wimbledon 2026 Fantasy Draft Tracker")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Auto refresh every 60s
st.markdown("<meta http-equiv='refresh' content='60'>", unsafe_allow_html=True)

api_data = fetch_live_data()
players = parse_data(api_data)
df = build_df(players)

if df.empty:
    st.info("Waiting for Wimbledon matches to start or API data...")
    st.stop()

df = add_clinch(df)

st.dataframe(df, use_container_width=True)

# -----------------------
# EXPORT BUTTON
# -----------------------
excel_bytes = df.to_excel(index=False)

st.download_button(
    label="📥 Download Excel",
    data=excel_bytes,
    file_name="wimbledon_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
``
