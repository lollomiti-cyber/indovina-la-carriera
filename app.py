import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

@st.cache_data
def load_data():
    players = pd.read_csv(DATA_PATH + "players.csv")
    transfers = pd.read_csv(DATA_PATH + "transfers.csv")
    
    return players, transfers

def is_first_team(club_name: str) -> bool:
    blacklist = ["U21", "U23" ,"U19", "U18", "U17", "Primavera", "Yth.", "Youth", " B", " II"]
    return not any(x in club_name for x in blacklist)

def season_to_year(season: str) -> int:
    # "2021/2022" → 21
    return int(season.split("/")[0][-2:])

def format_period(start_season: str, end_season: str, is_current=False) -> str:
    start_year = season_to_year(start_season)
    if is_current:
        return f"{start_year}-corrente"
    end_year = season_to_year(end_season) + 1
    return f"{start_year}-{end_year}"

def build_career(transfers_player: pd.DataFrame) -> pd.DataFrame:
    df = (
        transfers_player
        .sort_values("transfer_date")
        .reset_index(drop=True)
    )

    career_rows = []

    current_club = None
    start_year = None

    for _, row in df.iterrows():
        club = row["to_club_name"]
        year = int(row["transfer_season"].split("/")[0])

        if current_club is None:
            # primo stint
            current_club = club
            start_year = year

        elif club == current_club:
            # prestito, rientro, riscatto → IGNORA
            continue

        else:
            # nuovo club reale → chiudi stint precedente
            career_rows.append({
                "Squadra": current_club,
                "start_year": start_year,
                "end_year": year
            })
            current_club = club
            start_year = year

    # ultimo stint
    if current_club is not None:
        career_rows.append({
            "Squadra": current_club,
            "start_year": start_year,
            "end_year": None
        })

    # formatting finale
    output = []
    for row in career_rows:
        if row["end_year"] is None:
            period = f"{str(row['start_year'])[-2:]}-corrente"
        else:
            period = f"{str(row['start_year'])[-2:]}-{str(row['end_year'])[-2:]}"

        output.append({
            "Squadra": row["Squadra"],
            "Periodo": period
        })

    return pd.DataFrame(output)

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
transfers_player = transfers_player[transfers_player["to_club_name"].apply(is_first_team)]

career = build_career(transfers_player)

st.subheader("🏟️ Carriera")
st.dataframe(career, use_container_width=True)

if st.button("✅ Mostra soluzione"):
    name = players.loc[
        players["player_id"] == player_id, "player_name"
    ].iloc[0]
    st.success(f"Il giocatore era: {name}")

