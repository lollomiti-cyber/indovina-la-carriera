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

def year_from_date(date: pd.Timestamp) -> int:
    return date.year

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
    df = (
        transfers_player
        .sort_values("transfer_date")
        .reset_index(drop=True)
    )

    stints = []

    for _, row in df.iterrows():
        club = row["to_club_name"]
        year = year_from_date(row["transfer_date"])

        if not stints:
            stints.append({
                "club": club,
                "start": year,
                "end": None
            })
            continue

        last = stints[-1]

        # RUMORE: rientro nello stesso club
        if club == last["club"]:
            continue

        # vero cambio club
        last["end"] = year
        stints.append({
            "club": club,
            "start": year,
            "end": None
        })

    # formatting finale
    output = []
    for stint in stints:
        if stint["end"] is None:
            periodo = f"{str(stint['start'])[-2:]}-corrente"
        else:
            periodo = f"{str(stint['start'])[-2:]}-{str(stint['end'])[-2:]}"

        output.append({
            "Squadra": stint["club"],
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

