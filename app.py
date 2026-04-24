import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

@st.cache_data
def load_data():
    players = pd.read_csv(DATA_PATH + "players.csv")
    transfers = pd.read_csv(DATA_PATH + "transfers.csv")
    
    return players, transfers

def format_period(start_season: str, end_season: str) -> str:
    if start_season == end_season:
        return start_season
    else:
        return f"{start_season.split('/')[0]}/{end_season.split('/')[1]}"

def build_career(transfers_player: pd.DataFrame) -> pd.DataFrame:
    # Ordina per data
    df = transfers_player.sort_values("transfer_date").copy()

    # Tieni solo la prima destinazione per stagione
    df = df.drop_duplicates(subset=["transfer_season"], keep="first")

    career_rows = []

    current_club = None
    start_season = None
    last_season = None

    for _, row in df.iterrows():
        season = row["transfer_season"]
        club = row["to_club_name"]

        if current_club is None:
            current_club = club
            start_season = season
            last_season = season
        elif club == current_club:
            last_season = season
        else:
            career_rows.append({
                "Squadra": current_club,
                "Periodo": format_period(start_season, last_season)
            })
            current_club = club
            start_season = season
            last_season = season

    # Ultimo periodo
    if current_club is not None:
        career_rows.append({
            "Squadra": current_club,
            "Periodo": format_period(start_season, last_season)
        })

    return pd.DataFrame(career_rows)

players, transfers = load_data()

# Normalizzazioni base
transfers["transfer_date"] = pd.to_datetime(transfers["transfer_date"], errors="coerce")
transfers = transfers.sort_values("transfer_date")

st.title("⚽ Indovina la carriera")

if st.button("🔄 Nuova carriera"):
    st.session_state.player_id = random.choice(
        players["player_id"].unique()
    )

# Giocatore random
if "player_id" not in st.session_state:
    st.session_state.player_id = random.choice(
        players["player_id"].unique()
    )

player_id = st.session_state.player_id

transfers_player = transfers[transfers["player_id"] == player_id]

career = build_career(transfers_player)

st.subheader("🏟️ Carriera")
st.dataframe(career, use_container_width=True)

if st.button("✅ Mostra soluzione"):
    name = players.loc[
        players["player_id"] == player_id, "player_name"
    ].iloc[0]
    st.success(f"Il giocatore era: {name}")

