"""
Parses Cricsheet JSON match files (https://cricsheet.org/downloads/)
into matches, innings_scores, and partnerships.

Download a SMALL, FILTERED subset from Cricsheet — e.g. just Men's
ODIs from the last few years, or a single competition — and point
this script at that folder. Don't download the entire archive (10GB+);
a filtered subset is tens of MB and is enough for every SQL question
in this project.

Usage:
    python data/ingest_cricsheet.py path/to/cricsheet_json_folder/
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.db_connection import init_schema, get_connection


def get_or_create_player(cur, name: str) -> int:
    cur.execute("SELECT player_id FROM players WHERE player_name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row["player_id"]
    cur.execute("INSERT INTO players (player_name) VALUES (?)", (name,))
    return cur.lastrowid


def get_or_create_venue(cur, venue_name: str, city: str = "", country: str = "") -> int:
    cur.execute("SELECT venue_id FROM venues WHERE venue_name = ?", (venue_name,))
    row = cur.fetchone()
    if row:
        return row["venue_id"]
    cur.execute(
        "INSERT INTO venues (venue_name, city, country) VALUES (?, ?, ?)",
        (venue_name, city, country),
    )
    return cur.lastrowid


def parse_match_file(cur, path: Path):
    with open(path, "r") as f:
        data = json.load(f)

    info = data.get("info", {})
    teams = info.get("teams", [])
    if len(teams) != 2:
        return

    venue_name = info.get("venue", "Unknown")
    city = info.get("city", "")
    venue_id = get_or_create_venue(cur, venue_name, city)

    outcome = info.get("outcome", {})
    winner = outcome.get("winner")
    by = outcome.get("by", {})
    victory_margin = by.get("runs") or by.get("wickets")
    victory_type = "runs" if "runs" in by else ("wickets" if "wickets" in by else None)

    toss = info.get("toss", {})

    cur.execute(
        "INSERT INTO matches (description, team1, team2, venue_id, match_date, match_type, "
        "toss_winner, toss_decision, winner, victory_margin, victory_type, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')",
        (
            f"{teams[0]} vs {teams[1]}",
            teams[0],
            teams[1],
            venue_id,
            info.get("dates", [None])[0],
            info.get("match_type", ""),
            toss.get("winner"),
            toss.get("decision"),
            winner,
            victory_margin,
            victory_type,
        ),
    )
    match_id = cur.lastrowid
    match_date = info.get("dates", [None])[0]

    # --- innings: batting positions, runs, and simple partnership tracking ---
    for innings_no, innings in enumerate(data.get("innings", []), start=1):
        batting_order = []  # tracks (player, cumulative_runs) in order of appearance
        player_runs = {}
        player_balls = {}

        for over in innings.get("overs", []):
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter")
                runs = delivery.get("runs", {}).get("batter", 0)
                if batter not in player_runs:
                    player_runs[batter] = 0
                    player_balls[batter] = 0
                    batting_order.append(batter)
                player_runs[batter] += runs
                player_balls[batter] += 1

                bowler = delivery.get("bowler")
                wicket = delivery.get("wickets")
                # (bowling figures aggregation omitted here for brevity —
                # extend this loop to accumulate runs_conceded/wickets per bowler
                # the same way it's done for batters above)

        for pos, batter in enumerate(batting_order, start=1):
            player_id = get_or_create_player(cur, batter)
            runs = player_runs[batter]
            balls = player_balls[batter]
            sr = round(100 * runs / balls, 2) if balls else 0
            cur.execute(
                "INSERT INTO innings_scores (match_id, player_id, innings_no, batting_position, "
                "runs_scored, balls_faced, strike_rate, match_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (match_id, player_id, innings_no, pos, runs, balls, sr, match_date),
            )

        # Simple consecutive-position partnerships (adjacent batting order).
        for i in range(len(batting_order) - 1):
            p1_id = get_or_create_player(cur, batting_order[i])
            p2_id = get_or_create_player(cur, batting_order[i + 1])
            combined = player_runs[batting_order[i]] + player_runs[batting_order[i + 1]]
            cur.execute(
                "INSERT INTO partnerships (match_id, innings_no, player1_id, player2_id, "
                "wicket_number, partnership_runs) VALUES (?, ?, ?, ?, ?, ?)",
                (match_id, innings_no, p1_id, p2_id, i + 1, combined),
            )


def ingest(folder: str):
    init_schema()
    conn = get_connection()
    cur = conn.cursor()

    json_files = list(Path(folder).glob("*.json"))
    if not json_files:
        print(f"No .json files found in {folder}")
        return

    for i, path in enumerate(json_files, start=1):
        try:
            parse_match_file(cur, path)
        except Exception as e:
            print(f"Skipped {path.name}: {e}")
        if i % 25 == 0:
            conn.commit()
            print(f"...{i}/{len(json_files)} matches processed")

    conn.commit()
    conn.close()
    print(f"Done. Processed {len(json_files)} match files.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python data/ingest_cricsheet.py path/to/cricsheet_json_folder/")
        sys.exit(1)
    ingest(sys.argv[1])
