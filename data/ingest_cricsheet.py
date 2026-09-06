"""
Cricbuzz Livestats - Cricsheet Data Ingestion

Parses Cricsheet JSON match files into the SQLite database.

Supported data:
- Match details
- Players and venues
- Innings batting statistics
- Basic partnerships

Usage:
    python data/ingest_cricsheet.py path/to/cricsheet_json_folder/
"""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.db_connection import init_schema, get_connection


# Database helpers

def get_or_create_player(cur, name: str) -> int:
    cur.execute(
        "SELECT player_id FROM players WHERE player_name = ?",
        (name,),
    )

    row = cur.fetchone()

    if row:
        return row["player_id"]

    cur.execute(
        "INSERT INTO players (player_name) VALUES (?)",
        (name,),
    )

    return cur.lastrowid


def get_or_create_venue(
    cur,
    venue_name: str,
    city: str = "",
    country: str = "",
) -> int:
    cur.execute(
        "SELECT venue_id FROM venues WHERE venue_name = ?",
        (venue_name,),
    )

    row = cur.fetchone()

    if row:
        return row["venue_id"]

    cur.execute(
        """
        INSERT INTO venues (venue_name, city, country)
        VALUES (?, ?, ?)
        """,
        (venue_name, city, country),
    )

    return cur.lastrowid


# Match parsing

def parse_match_file(cur, path: Path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    info = data.get("info", {})
    teams = info.get("teams", [])

    if len(teams) != 2:
        return

    venue_name = info.get("venue", "Unknown")
    city = info.get("city", "")

    venue_id = get_or_create_venue(
        cur,
        venue_name,
        city,
    )

    outcome = info.get("outcome", {})
    winner = outcome.get("winner")
    by = outcome.get("by", {})

    victory_margin = by.get("runs") or by.get("wickets")

    victory_type = (
        "runs"
        if "runs" in by
        else "wickets"
        if "wickets" in by
        else None
    )

    toss = info.get("toss", {})
    match_date = info.get("dates", [None])[0]

    cur.execute(
        """
        INSERT INTO matches (
            description,
            team1,
            team2,
            venue_id,
            match_date,
            match_type,
            toss_winner,
            toss_decision,
            winner,
            victory_margin,
            victory_type,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')
        """,
        (
            f"{teams[0]} vs {teams[1]}",
            teams[0],
            teams[1],
            venue_id,
            match_date,
            info.get("match_type", ""),
            toss.get("winner"),
            toss.get("decision"),
            winner,
            victory_margin,
            victory_type,
        ),
    )

    match_id = cur.lastrowid

    # Process innings

    for innings_no, innings in enumerate(
        data.get("innings", []),
        start=1,
    ):
        batting_order = []
        player_runs = {}
        player_balls = {}

        for over in innings.get("overs", []):
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter")

                runs = delivery.get(
                    "runs",
                    {},
                ).get(
                    "batter",
                    0,
                )

                if batter not in player_runs:
                    player_runs[batter] = 0
                    player_balls[batter] = 0
                    batting_order.append(batter)

                player_runs[batter] += runs
                player_balls[batter] += 1

        # Store batting statistics

        for position, batter in enumerate(
            batting_order,
            start=1,
        ):
            player_id = get_or_create_player(
                cur,
                batter,
            )

            runs = player_runs[batter]
            balls = player_balls[batter]

            strike_rate = (
                round(100 * runs / balls, 2)
                if balls
                else 0
            )

            cur.execute(
                """
                INSERT INTO innings_scores (
                    match_id,
                    player_id,
                    innings_no,
                    batting_position,
                    runs_scored,
                    balls_faced,
                    strike_rate,
                    match_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    player_id,
                    innings_no,
                    position,
                    runs,
                    balls,
                    strike_rate,
                    match_date,
                ),
            )

        # Store basic partnerships

        for index in range(
            len(batting_order) - 1
        ):
            player1 = batting_order[index]
            player2 = batting_order[index + 1]

            player1_id = get_or_create_player(
                cur,
                player1,
            )

            player2_id = get_or_create_player(
                cur,
                player2,
            )

            partnership_runs = (
                player_runs[player1]
                + player_runs[player2]
            )

            cur.execute(
                """
                INSERT INTO partnerships (
                    match_id,
                    innings_no,
                    player1_id,
                    player2_id,
                    wicket_number,
                    partnership_runs
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id,
                    innings_no,
                    player1_id,
                    player2_id,
                    index + 1,
                    partnership_runs,
                ),
            )


# Data ingestion

def ingest(folder: str):
    init_schema()

    conn = get_connection()
    cur = conn.cursor()

    json_files = list(
        Path(folder).glob("*.json")
    )

    if not json_files:
        print(
            f"No .json files found in {folder}"
        )
        conn.close()
        return

    total_files = len(json_files)

    for index, path in enumerate(
        json_files,
        start=1,
    ):
        try:
            parse_match_file(
                cur,
                path,
            )

        except Exception as error:
            print(
                f"Skipped {path.name}: {error}"
            )

        if index % 25 == 0:
            conn.commit()

            print(
                f"...{index}/{total_files} "
                "matches processed"
            )

    conn.commit()
    conn.close()

    print(
        f"Done. Processed {total_files} match files."
    )


# Entry point

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python "
            "data/ingest_cricsheet.py "
            "path/to/cricsheet_json_folder/"
        )
        sys.exit(1)

    ingest(sys.argv[1])