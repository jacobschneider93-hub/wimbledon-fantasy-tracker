import streamlit as st
import pandas as pd
import requests
import random

st.set_page_config(layout="wide")

# -----------------------
# PLAYER MAP + ACE RATES
# -----------------------
players_info = {
    "Taylor Fritz": ("Villani", 10),
    "Daniil Medvedev": ("Jesse", 6),
    "Andrey Rublev": ("Sam", 7),
    "Casper Ruud": ("Schur", 5),
    "Felix Auger-Aliassime": ("Will", 12),
    "Ben Shelton": ("Hunter", 15),
    "Novak Djokovic": ("Shanfeldt", 8),
    "Alexander Zverev": ("Dylan", 9),
    "Flavio Cobolli": ("Shahar", 4),
    "Alex de Minaur": ("Schneider", 3),
    "Jannik Sinner": ("Kevin", 9),
    "Alexander Bublik": ("Eran", 18)
}

# -----------------------
# FETCH DATA (FREE API)
# -----------------------
@st.cache_data(ttl=60)
def fetch_data():
    url = "https://sportscore.com/api/widget/matches?sport=tennis"
    res = requests.get(url)
    return res.json().get("matches", [])

# -----------------------
# PARSE DATA
# -----------------------
def parse(matches):
    stats = {}

    for match in matches:
        comp = match.get("competition", "").lower()

        # ✅ Wimbledon filter
        if "wimbledon" not in comp:
            continue

        home = match.get("home", {}).get("name")
        away = match.get("away", {}).get("name")

        for p in [home, away]:
            if p in players_info and p not in stats:
                stats[p] = {
                    "Matches Won": 0,
                    "Sets Won": 0,
                    "Games Won": 0,
                    "Aces": 0
                }

        # Winner
        winner = match.get("winner")

        if winner == "home" and home in stats:
            stats[home]["Matches Won"] += 1
        elif winner == "away" and away in stats:
            stats[away]["Matches Won"] += 1

        # Score parsing
        score = match.get("score", "")
        sets = score.split(" ")

        for s in sets:
            try:
                h, a = map(int, s.split("-"))

                if home in stats:
                    stats[home]["Games Won"] += h
                    stats[home]["Sets Won"] += int(h > a)

                    # Estimate aces
                    stats[home]["Aces"] += players_info[home][1] * (h / 12)

                if away in stats:
                    stats[away]["Games Won"] += a
                    stats[away]["Sets Won"] += int(a > h)
                    stats[away]["Aces"] += players_info[away][1] * (a / 12)

            except:
                continue

    return stats

# -----------------------
# BUILD RANKINGS
# -----------------------
def build(stats):
    rows = []
    for p, s in stats.items():
        rows.append({
            "Player": p,
            "Manager": players_info[p][0],
            **s
        })

    df = pd.DataFrame(rows)

    df = df.sort_values(
        by=["Matches Won", "Sets Won", "Aces", "Games Won"],
        ascending=[False, False, False, False]
    )

    df["Rank"] = range(1, len(df)+1)
    return df

# -----------------------
# PROJECTION ENGINE
# -----------------------
def simulate(df, sims=1000):
    results = {p: [] for p in df["Player"]}

    for _ in range(sims):
        sim_df = df.copy()

        # Random future wins
        for i in range(len(sim_df)):
            sim_df.loc[i, "Matches Won"] += random.choice([0,1,2])

        sim_df = sim_df.sort_values(
            by=["Matches Won", "Sets Won", "Aces", "Games Won"],
            ascending=[False, False, False, False]
        )

        sim_df["Rank"] = range(1, len(sim_df)+1)

        for _, row in sim_df.iterrows():
            results[row["Player"]].append(row["Rank"])

    # Avg finish
    avg_finish = {
        p: round(sum(r)/len(r), 2)
        for p,r in results.items()
    }

    return avg_finish

# -----------------------
# CLINCH LOGIC
# -----------------------
def clinch(df):
    df["Clinched"] = False

    max_matches_left = 3  # adjustable

    for i in range(len(df)):
        leader = df.iloc[i]

        safe = True
        for j in range(i+1, len(df)):
            challenger = df.iloc[j]

            if challenger["Matches Won"] + max_matches_left >= leader["Matches Won"]:
                safe = False

        if safe:
            df.at[df.index[i], "Clinched"] = True

    return df

# -----------------------
# UI
# -----------------------
st.title("🏆 Wimbledon Fantasy Draft Tracker (ELITE MODE)")

matches = fetch_data()
stats = parse(matches)

if not stats:
    st.warning("No Wimbledon data yet")
    st.stop()

df = build(stats)
df = clinch(df)

# ✅ projections
projections = simulate(df)
df["Projected Finish"] = df["Player"].map(projections)

# Display
st.dataframe(df, use_container_width=True)

# -----------------------
# VISUALS
# -----------------------
st.subheader("📊 Aces Leaderboard")
st.bar_chart(df.set_index("Player")["Aces"])

st.subheader("📈 Projected Draft Order")
st.bar_chart(df.set_index("Player")["Projected Finish"])

# -----------------------
# EXPORT
# -----------------------
st.download_button(
    "📥 Download Results",
    df.to_excel(index=False),
    "wimbledon_results.xlsx"
)
