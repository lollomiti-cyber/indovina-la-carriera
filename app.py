import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

# =========================
# CONFIG
# =========================

MIN_REAL_STINT_DAYS = 30
MAX_ATTEMPTS = 3
BIG_CLUBS_IDS = [506, 46, 5, 6195, 12]  # Juve, Inter, Milan, Napoli, Roma
SEMI_BIG_CLUBS_IDS = [1025, 430, 398, 800]
LEVELS = {
    1: {"level": 1},
    2: {"level": 2},
    3: {"level": 3},
}

# =========================
# DATA LOADING
# =========================

@st.cache_data
def load_data():
    players = pd.read_csv(DATA_PATH + "players.csv")
    transfers = pd.read_csv(DATA_PATH + "transfers.csv")
    clubs = pd.read_csv(DATA_PATH + "clubs.csv")
    return players, transfers, clubs

# =========================
# UTILS
# =========================


def get_pool(config):

    if config["level"] == 1:
        return players_big

    elif config["level"] == 2:
        return players_level2

    else:
        return players_level3


def is_first_team(club_name: str) -> bool:
    blacklist = [
        "U15", "U17", "U18", "U19",
        "Primavera", "Youth", " B", " II", "Yth."
    ]
    return not any(x in club_name for x in blacklist)

# =========================
# CORE LOGIC
# =========================

def reset_game():
    pool = get_pool(config)
    st.session_state.player_id = random.choice(pool)
    st.session_state.attempts_left = MAX_ATTEMPTS
    st.session_state.solved = False
    st.session_state.guess_input = None
    

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

players, transfers, clubs = load_data()

transfers["transfer_date"] = pd.to_datetime(transfers["transfer_date"], errors="coerce")
transfers = transfers.dropna(subset=["transfer_date"])
italian_clubs_ids = clubs[clubs["domestic_competition_id"] == "IT1"]["club_id"].unique()
players_italy = transfers[(transfers["to_club_id"].isin(italian_clubs_ids)) | (transfers["from_club_id"].isin(italian_clubs_ids))]["player_id"].unique()
players_big = transfers[((transfers["to_club_id"].isin(BIG_CLUBS_IDS)) | (transfers["from_club_id"].isin(BIG_CLUBS_IDS))) & (transfers["player_id"].isin(players_italy))]["player_id"].unique()
players_semi_big = transfers[((transfers["to_club_id"].isin(SEMI_BIG_CLUBS_IDS)) | (transfers["from_club_id"].isin(SEMI_BIG_CLUBS_IDS))) & (transfers["player_id"].isin(players_italy))]["player_id"].unique()
players_level2 = [pid for pid in players_semi_big if pid not in players_big]
players_level3 = [pid for pid in players_italy if pid not in players_big and pid not in players_semi_big]

# ✅ DEFINITO QUI (PRIMA DEL LAYOUT)

st.title("⚽ Indovina la carriera 🇮🇹")

level = st.selectbox(
    "🎚️ Livello",
    options=[1, 2, 3],
    format_func=lambda x: f"Livello {x}"
)
config = LEVELS[level]
pool = get_pool(config)


player_names = players[players["player_id"].isin(pool)]["player_name"].sort_values().unique()

if "last_level" not in st.session_state:
    st.session_state.last_level = level

if level != st.session_state.last_level:
    reset_game()
    st.session_state.last_level = level

# Stato
if "player_id" not in st.session_state:
    reset_game()

if "attempts_left" not in st.session_state:
    st.session_state.attempts_left = MAX_ATTEMPTS

if "solved" not in st.session_state:
    st.session_state.solved = False

# Nuova carriera
if st.button("🔄 Reset game"):
    reset_game()

player_id = st.session_state.player_id

# Trasferimenti giocatore
transfers_player = transfers[
    transfers["player_id"] == player_id
]

transfers_player = transfers_player[
    transfers_player["to_club_name"].apply(is_first_team)
]

career = build_career(transfers_player)

# =========================
# LAYOUT
# =========================

col_input, col_career = st.columns([1, 3])

with col_input:
    st.info(f"🎯 Tentativi rimasti: {st.session_state.attempts_left}")

    guess = st.selectbox(
        "✍️ Chi è il giocatore?",
        options=player_names,
        index=None,
        placeholder="Inizia a scrivere il nome...",
        disabled=st.session_state.solved,
        key="guess_input"
    )

    if st.button("👁️ Rivela giocatore"):
        solution = players.loc[
            players["player_id"] == player_id, "player_name"
        ].iloc[0]
        st.warning(f"✅ Il giocatore era: **{solution}**")
        st.session_state.solved = True

with col_career:
    st.subheader("🏟️ Carriera")
    st.table(career)

# =========================
# VERIFICA RISPOSTA
# =========================

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
