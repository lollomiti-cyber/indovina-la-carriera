import streamlit as st
import pandas as pd
import random

DATA_PATH = "data/"

@st.cache_data
def load_data():
    players = pd.read_csv(DATA_PATH + "players.csv")
    transfers = pd.read_csv(DATA_PATH + "transfers.csv")
    return players, transfers

players, transfers = load_data()

# Normalizzazioni base
transfers["transfer_date"] = pd.to_datetime(transfers["transfer_date"], errors="coerce")
transfers = transfers.sort_values("transfer_date")

st.title("⚽ Indovina la carriera")

# Giocatore random
player_id = random.choice(players["player_id"].unique())

career = (
    transfers[transfers["player_id"] == player_id]
    [["transfer_season", "from_club_name", "to_club_name"]]
    .rename(columns={
        "transfer_season": "Stagione",
        "from_club_name": "Da",
        "to_club_name": "A"
    })
    .reset_index(drop=True)
)

st.subheader("📜 Trasferimenti")
st.dataframe(career, use_container_width=True)

if st.button("✅ Mostra soluzione"):
    name = players.loc[
        players["player_id"] == player_id, "name"
    ].iloc[0]
    st.success(f"Il giocatore era: **{name}**")
