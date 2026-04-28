import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

# =========================
# DATA LOADING
# =========================

@st.cache_data
def load_data():
    players = pd.read_csv(DATA_PATH + "players.csv")
    transfers = pd.read_csv(DATA_PATH + "transfers.csv")
    return players, transfers


# =========================
# UTILS
# =========================

def is_first_team(club_name: str) -> bool:
    blacklist = [
        "U17", "U18", "U19", "Primavera",
        "Youth", "B", "II"
    ]
    return not any(x in club_name for x in blacklist)


def season_start_year(season: str) -> int:
    # "2018/2019" -> 2018
    return int(season.split("/")[0])


# =========================
# CORE LOGIC
# =========================

def final_club_per_season(transfers_player: pd.DataFrame) -> pd.DataFrame:
    """
    Per ogni stagione tiene SOLO il club finale
    (risolve prestiti + rientri + riscatti)
    """
    df = transfers_player.sort_values("transfer_date")

    df = (
        df.groupby("transfer_season", as_index=False)
        .last()
        .sort_values("transfer_season")
        .reset_index(drop=True)
    )

    return df


def build_career(transfers_player: pd.DataFrame) -> pd.DataFrame:
    df = final_club_per_season(transfers_player)

    career_rows = []

    current_club = None
    start_year = None

    for _, row in df.iterrows():
        club = row["to_club_name"]
        year = season_start_year(row["transfer_season"])

        if current_club is None:
            current_club = club
            start_year = year

        elif club != current_club:
            career_rows.append({
                "Squadra": current_club,
                "start": start_year,
                "end": year
            })
            current_club = club
            start_year = year

    # ultimo stint
    if current_club is not None:
        career_rows.append({
            "Squadra": current_club,
            "start": start_year,
            "end": None
        })

    # formatting finale
    output = []
    for c in career_rows:
        if c["end"] is None:
            periodo = f"{str(c['start'])[-2:]}-corrente"
        else:
            periodo = f"{str(c['start'])[-2:]}-{str(c['end'])[-2:]}"

        output.append({
            "Squadra": c["Squadra"],
            "Periodo": periodo
        })

    return pd.DataFrame(output)


# =========================
# APP
# =========================

players, transfers = load_data()

transfers["transfer_date"] = pd.to_datetime(
    transfers["transfer_date"],
    errors="coerce"
)

st.title("⚽ Indovina la carriera")

if st.button("🔄 Nuova carriera"):
    st.session_state.player_id = random.choice(
        players["player_id"].unique()
    )

if "player_id" not in st.session_state:
    st.session_state.player_id = random.choice(
        players["player_id"].unique()
    )

player_id = st.session_state.player_id

# filtra trasferimenti del giocatore
transfers_player = transfers[
    transfers["player_id"] == player_id
]

# filtra solo prime squadre
transfers_player = transfers_player[
    transfers_player["to_club_name"].apply(is_first_team)
]

career = build_career(transfers_player)

st.subheader("🏟️ Carriera")
st.table(career)

if st.button("✅ Mostra soluzione"):
    name = players.loc[
        players["player_id"] == player_id, "player_name"
    ].iloc[0]
    st.success(f"Il giocatore era: {name}")
``
