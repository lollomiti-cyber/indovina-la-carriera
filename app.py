import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

# =========================
# CONFIG
# =========================

MIN_REAL_STINT_DAYS = 30
MAX_ATTEMPTS = 3

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
        "Youth", " B", " II", "Yth."
    ]
    return not any(x in club_name for x in blacklist)

# =========================
# CORE LOGIC
# =========================

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

        # durata fino al prossimo trasferimento
        if i < len(df) - 1:
            next_date = df.iloc[i + 1]["transfer_date"]
            duration_days = (next_date - start_date).days
        else:
            duration_days = None

        if not stints:
            stints.append({
                "club": club,
                "start_date": start_date,
                "end_date": None
            })
            continue

        last = stints[-1]

        # RUMORE: rientro nello stesso club
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
            periodo = f"{start_year}-corrente"
        else:
            end_year = stint["end_date"].year

            if start_year == end_year:
                periodo = f"{start_year}"
            else:
                periodo = f"{start_year}-{end_year}"

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

# Inizializzazione stato
if "player_id" not in st.session_state:
    st.session_state.player_id = random.choice(players["player_id"].unique())

if "attempts_left" not in st.session_state:
    st.session_state.attempts_left = MAX_ATTEMPTS

if "solved" not in st.session_state:
    st.session_state.solved = False

# Nuova carriera
if st.button("🔄 Nuova carriera"):
    st.session_state.player_id = random.choice(players["player_id"].unique())
    st.session_state.attempts_left = MAX_ATTEMPTS
    st.session_state.solved = False

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

# Tentativi rimasti
st.info(f"🎯 Tentativi rimasti: {st.session_state.attempts_left}")

# Input con suggerimenti live
player_names = players["player_name"].sort_values().unique()

if st.button("👁️ Rivela giocatore"):
    solution = players.loc[
        players["player_id"] == player_id, "player_name"
    ].iloc[0]

    st.warning(f"✅ Il giocatore era: **{solution}**")
    st.session_state.solved = True

guess = st.selectbox(
    "✍️ Chi è il giocatore?",
    options=player_names,
    index=None,
    placeholder="Inizia a scrivere il nome...",
    disabled=st.session_state.solved
)

st.subheader("🏟️ Carriera")
st.table(career)

# Verifica risposta
if guess and not st.session_state.solved:
    solution = players.loc[
        players["player_id"] == player_id, "player_name"
    ].iloc[0]

    if guess == solution:
        st.success("🎉 Bravo! Giocatore indovinato!")
        st.session_state.solved = True
    else:
        st.session_state.attempts_left -= 1

        if st.session_state.attempts_left > 0:
            st.error("❌ Non è lui, riprova!")
        else:
            st.error("❌ Tentativi esauriti!")
            st.warning(f"✅ Il giocatore era: **{solution}**")
            st.session_state.solved = True
