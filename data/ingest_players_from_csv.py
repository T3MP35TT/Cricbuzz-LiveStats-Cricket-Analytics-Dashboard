"""
Loads a Kaggle player career-stats CSV into
players + player_career_stats.

Usage:
    python data/ingest_players_from_csv.py path/to/player_stats.csv

Expected input columns:
    player_name, country, playing_role, batting_style, bowling_style,
    format, matches, runs, batting_average, strike_rate, hundreds,
    fifties, highest_score, wickets, bowling_average, economy, catches, stumpings
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.db_connection import init_schema, get_connection


# Column mapping

COLUMN_MAP = {
    "player_name": "player_name",
    "country": "country",
    "playing_role": "playing_role",
    "batting_style": "batting_style",
    "bowling_style": "bowling_style",
    "format": "format",
    "matches": "matches_played",
    "runs": "runs_scored",
    "batting_average": "batting_average",
    "strike_rate": "strike_rate",
    "hundreds": "hundreds",
    "fifties": "fifties",
    "highest_score": "highest_score",
    "wickets": "wickets_taken",
    "bowling_average": "bowling_average",
    "economy": "economy_rate",
    "catches": "catches",
    "stumpings": "stumpings",
}


def ingest(csv_path: str):
    init_schema()
    df = pd.read_csv(csv_path)

    missing = [c for c in COLUMN_MAP if c not in df.columns]
    if missing:
        print(f"WARNING: these expected columns are not in the CSV: {missing}")
        print(f"Available columns: {list(df.columns)}")
        print("Edit COLUMN_MAP in this script to match, then re-run.")
        return

    conn = get_connection()
    cur = conn.cursor()
    inserted_players, inserted_stats = 0, 0

    for _, row in df.iterrows():
        name = str(row.get("player_name", "")).strip()
        if not name or name.lower() == "nan":
            continue

        cur.execute(
            "INSERT OR IGNORE INTO players (player_name, country, playing_role, batting_style, bowling_style) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                name,
                row.get("country", ""),
                row.get("playing_role", ""),
                row.get("batting_style", ""),
                row.get("bowling_style", ""),
            ),
        )
        if cur.rowcount:
            inserted_players += 1

        cur.execute("SELECT player_id FROM players WHERE player_name = ?", (name,))
        result = cur.fetchone()
        if not result:
            continue
        player_id = result["player_id"]

        cur.execute(
            "INSERT OR IGNORE INTO player_career_stats "
            "(player_id, format, matches_played, runs_scored, batting_average, strike_rate, "
            "hundreds, fifties, highest_score, wickets_taken, bowling_average, economy_rate, catches, stumpings) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                player_id,
                row.get("format", ""),
                row.get("matches", 0),
                row.get("runs", 0),
                row.get("batting_average", None),
                row.get("strike_rate", None),
                row.get("hundreds", 0),
                row.get("fifties", 0),
                row.get("highest_score", None),
                row.get("wickets", 0),
                row.get("bowling_average", None),
                row.get("economy", None),
                row.get("catches", 0),
                row.get("stumpings", 0),
            ),
        )
        if cur.rowcount:
            inserted_stats += 1

    conn.commit()
    conn.close()
    print(f"Done. Inserted {inserted_players} new players, {inserted_stats} career-stat rows.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python data/ingest_players_from_csv.py path/to/player_stats.csv")
        sys.exit(1)
    ingest(sys.argv[1])