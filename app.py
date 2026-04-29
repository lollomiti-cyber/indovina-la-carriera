import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

# =========================
# DATA LOADING
# =========================

MIN_REAL_STINT_DAYS = 30

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
        "Youth", " B", " II", "Yth."
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

    for i, row in df.iterrows():
        club = row["to_club_name"]
        start_date = row["transfer_date"]
        start_year = start_date.year

        # durata fino al prossimo trasferimento
        if i < len(df) - 1:
            next_date = df.iloc[i + 1]["transfer_date"]
            duration_days = (next_date - start_date).days
        else:
            duration_days = None  # ultimo club

        if not stints:
            stints.append({
                "club": club,
                "start_date": start_date,
                "end_date": None
            })
            continue

        last = stints[-1]

        # RUMORE: ritorno allo stesso club
        if club == last["club"]:
            continue

        # RUMORE: permanenza troppo breve
        if duration_days is not None and duration_days < MIN_REAL_STINT_DAYS:
            continue

        # cambio reale
        last["end_date"] = start_date
        stints.append({
            "club": club,
            "start_date": start_date,
            "end_date": None
        })

    # FORMAT UX
    output = []
    for stint in stints:
        start_year = stint["start_date"].year

        if stint["end_date"] is None:
            periodo = f"{str(start_year)}-corrente"
        else:
            end_year = stint["end_date"].year

            if start_year == end_year:
                periodo = f"{start_year}"
            else:
                periodo = f"{str(start_year)}-{str(end_year)}"

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

player_names = players["player_name"].sort_values().unique()

guess = st.selectbox(
    "✍️ Chi è il giocatore?",
    options=player_names,
    index=None,
    placeholder="Inizia a scrivere il nome..."
)

if guess:
    solution = players.loc[
        players["player_id"] == player_id, "player_name"
    ].iloc[0]

    if guess == solution:
        st.success("🎉 Bravo! Giocatore indovinato!")
    else:
        st.error("❌ Non è lui, riprova!")
