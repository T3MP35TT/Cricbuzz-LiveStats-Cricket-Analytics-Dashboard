import html
import sys
import json
from pathlib import Path

import pandas as pd
import streamlit as st


# Project root

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.api_helper import (
    get_live_matches,
    get_recent_matches,
    get_match_scorecard,
)
from utils.gamification import (
    init_game_state,
    add_xp,
    complete_mission,
)
from utils.theme import apply_theme


# Page configuration

st.set_page_config(
    page_title="Live Matches | Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
)


# Sidebar navigation

st.markdown(
    """
    <style>

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                rgba(5, 8, 16, 0.98),
                rgba(8, 11, 20, 0.98)
            ) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebarNav"] {
        padding: 18px 12px 14px 12px !important;
    }

    [data-testid="stSidebarNav"] ul {
        padding: 0 !important;
        margin: 0 !important;
        gap: 6px !important;
    }

    [data-testid="stSidebarNav"] li {
        margin: 0 !important;
        padding: 0 !important;
    }

    [data-testid="stSidebarNav"] a {
        position: relative !important;
        display: flex !important;
        align-items: center !important;

        min-height: 44px !important;
        box-sizing: border-box !important;

        padding: 0 16px !important;
        margin: 0 !important;

        border-radius: 11px !important;
        border: 1px solid transparent !important;

        background: transparent !important;

        color: rgba(255,255,255,0.78) !important;

        font-size: 14px !important;
        font-weight: 600 !important;

        text-decoration: none !important;

        transition:
            background 0.18s ease,
            border-color 0.18s ease,
            color 0.18s ease,
            transform 0.18s ease,
            box-shadow 0.18s ease !important;
    }

    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    [data-testid="stSidebarNav"] a::before {
        content: "" !important;

        width: 5px !important;
        height: 5px !important;
        min-width: 5px !important;

        margin-right: 14px !important;

        border-radius: 50% !important;

        background: rgba(255,255,255,0.18) !important;

        flex: 0 0 5px !important;

        transition:
            background 0.18s ease,
            box-shadow 0.18s ease !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;

        background: rgba(255,255,255,0.075) !important;

        border-color: rgba(255,255,255,0.10) !important;

        transform: translateX(2px) !important;

        box-shadow:
            0 5px 16px rgba(0,0,0,0.18) !important;
    }

    [data-testid="stSidebarNav"] a:hover::before {
        background: rgba(180,185,255,0.70) !important;

        box-shadow:
            0 0 7px rgba(160,165,255,0.45) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;

        background:
            linear-gradient(
                90deg,
                rgba(120,126,255,0.24),
                rgba(115,120,220,0.13)
            ) !important;

        border: 1px solid rgba(145,150,255,0.38) !important;

        box-shadow:
            inset 3px 0 0 rgba(180,185,255,0.98),
            0 7px 20px rgba(0,0,0,0.24) !important;

        font-weight: 800 !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]::before {
        background: #c9ccff !important;

        box-shadow:
            0 0 9px rgba(170,175,255,0.85) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]:hover {
        transform: translateX(1px) !important;
        border-color: rgba(160,165,255,0.48) !important;
    }

    [data-testid="stSidebarNav"]::after {
        content: "CRICBUZZ LIVESTATS";

        display: block;

        margin: 18px 8px 0 16px;
        padding-top: 14px;

        border-top: 1px solid rgba(255,255,255,0.09);

        color: rgba(255,255,255,0.28);

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 1.5px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# Sidebar live scores
# Display below Streamlit page navigation
sidebar_live_placeholder = st.sidebar.empty()


def _sidebar_score_value(team_score):
    if not isinstance(team_score, dict):
        return "—"
    innings = get_latest_innings(team_score)
    if not innings:
        return "—"
    runs = innings.get("runs")
    wickets = innings.get("wickets", 0)
    overs = innings.get("overs")
    if runs is None:
        return "—"
    if overs not in (None, ""):
        return f"{runs}/{wickets} ({overs})"
    return f"{runs}/{wickets}"


def _get_sidebar_live_matches(live_data):
    matches = []
    if not isinstance(live_data, dict) or "error" in live_data:
        return matches

    for type_block in live_data.get("typeMatches", []):
        for series in type_block.get("seriesMatches", []):
            series_data = series.get("seriesAdWrapper", {})
            for match_block in series_data.get("matches", []):
                info = match_block.get("matchInfo", {})
                status = info.get("status", "")
                if is_completed_match(status):
                    continue

                score = match_block.get("matchScore", {})
                team1 = info.get("team1", {})
                team2 = info.get("team2", {})

                match_id = info.get("matchId")
                matches.append({
                    "team1": team1.get("teamName", "Team 1"),
                    "team2": team2.get("teamName", "Team 2"),
                    "score1": _sidebar_score_value(score.get("team1Score", {})),
                    "score2": _sidebar_score_value(score.get("team2Score", {})),
                    "format": info.get("matchFormat", ""),
                    "status": status,
                    "match_id": match_id,
                })

    return matches


def render_sidebar_live_scores(live_data):
    matches = _get_sidebar_live_matches(live_data)
    cards = matches[:4]

    parts = [
        '<div class="sidebar-live-wrap">',
        '<div class="sidebar-live-heading"><span class="sidebar-live-dot"></span><span>LIVE NOW</span></div>',
    ]

    if not cards:
        parts.append('<div class="sidebar-no-live">No live matches right now.</div>')
    else:
        for match in cards:
            fmt = str(match["format"]).upper() if match["format"] else "LIVE"
            status = match["status"] or "Live match"
            if len(status) > 58:
                status = status[:55] + "..."

            card = (
                '<div class="sidebar-match-card">'
                f'<div class="sidebar-match-meta"><span>{fmt}</span><span class="sidebar-live-label">● LIVE</span></div>'
                f'<div class="sidebar-team-row"><a class="sidebar-team-name" href="{get_cricbuzz_match_url(match.get("match_id"))}" target="_blank">{html.escape(str(match["team1"]))}</a><strong class="sidebar-team-score">{html.escape(str(match["score1"]))}</strong></div>'
                f'<div class="sidebar-team-row"><a class="sidebar-team-name" href="{get_cricbuzz_match_url(match.get("match_id"))}" target="_blank">{html.escape(str(match["team2"]))}</a><strong class="sidebar-team-score">{html.escape(str(match["score2"]))}</strong></div>'
                f'<div class="sidebar-match-status">{status}</div>'
                '</div>'
            )
            parts.append(card)

        if len(matches) > 4:
            remaining = len(matches) - 4
            suffix = "es" if remaining != 1 else ""
            parts.append(f'<div class="sidebar-more-live">+{remaining} more live match{suffix}</div>')

    parts.append('</div>')
    sidebar_live_placeholder.markdown("".join(parts), unsafe_allow_html=True)

init_game_state()

apply_theme(
    badge_text="🔴 LIVE MATCHES • CRICKET ANALYTICS ARENA",
    title="Live Matches",
    subtitle="Follow live scores, dive into scorecards, and call the winner",
    tagline="🔥 LIVE SCORES &nbsp; • &nbsp; 🔮 PREDICTIONS &nbsp; • &nbsp; 🧾 SCORECARD XP",
)


st.markdown(
    """
    <style>
    .cricbuzz-subtitle {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }

    .cricbuzz-tagline {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    .sidebar-live-wrap {
        margin: 18px 4px 0 4px;
        padding-top: 14px;
        border-top: 1px solid rgba(255,255,255,0.09);
    }
    .sidebar-live-heading {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 8px 10px 8px;
        color: rgba(255,255,255,0.86);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.3px;
    }
    .sidebar-live-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #ff5c67;
        box-shadow: 0 0 9px rgba(255,92,103,0.75);
    }
    .sidebar-match-card {
        margin: 0 0 10px 0;
        padding: 11px;
        border-radius: 12px;
        background: linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 7px 18px rgba(0,0,0,0.18);
    }
    .sidebar-match-meta {
        display: flex;
        justify-content: space-between;
        margin-bottom: 7px;
        color: rgba(255,255,255,0.45);
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.8px;
    }
    .sidebar-live-label { color: #ff8b92; font-size: 8px; }
    .sidebar-team-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 7px;
        padding: 4px 0;
    }
    .sidebar-team-name {
        min-width: 0;
        text-decoration: none !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: rgba(255,255,255,0.86);
        font-size: 11px;
        font-weight: 700;
    }
    .sidebar-team-score {
        flex-shrink: 0;
        color: #ffffff;
        font-size: 12px;
        font-weight: 900;
    }
    .sidebar-match-status {
        margin-top: 5px;
        padding-top: 7px;
        border-top: 1px solid rgba(255,255,255,0.07);
        color: rgba(255,255,255,0.46);
        font-size: 9px;
        line-height: 1.35;
    }
    .sidebar-no-live {
        padding: 12px;
        border-radius: 11px;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.07);
        color: rgba(255,255,255,0.48);
        font-size: 10px;
    }
    .sidebar-more-live {
        margin: 2px 8px 0 8px;
        color: rgba(255,255,255,0.35);
        font-size: 9px;
        font-weight: 700;
        text-align: center;
    }

    /* Main live cards styled to match the compact Recent Matches cards. */
    .live-card-date {
        color: rgba(255,255,255,0.55);
        font-size: 10px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .live-card-team-link {
        display: block;
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 14px;
        font-weight: 800;
        line-height: 1.25;
        margin: 2px 0;
    }
    .live-card-team-link:hover {
        color: #c5caff !important;
        text-decoration: underline !important;
    }
    .live-card-vs {
        color: rgba(255,255,255,0.40);
        font-size: 10px;
        font-weight: 700;
        margin: 2px 0;
    }
    .live-card-score-box {
        min-height: 72px;
        padding: 10px 6px 8px 6px;
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        text-align: center;
        background: rgba(3,7,15,0.24);
        box-sizing: border-box;
    }
    .live-card-score-team {
        color: rgba(255,255,255,0.58);
        font-size: 9px;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .live-card-score {
        color: #ffffff;
        font-size: 19px;
        font-weight: 900;
        line-height: 1.15;
        margin-top: 7px;
    }
    .live-card-score-label {
        color: rgba(255,255,255,0.42);
        font-size: 8px;
        margin-top: 3px;
    }
    .live-card-status {
        margin: 9px 0 8px 0;
        padding: 8px 9px;
        border-radius: 9px;
        background: rgba(0, 150, 110, 0.13);
        border: 1px solid rgba(50, 180, 140, 0.16);
        color: rgba(255,255,255,0.72);
        font-size: 9px;
        line-height: 1.35;
    }
    .live-card-details {
        color: rgba(255,255,255,0.48);
        font-size: 9px;
        line-height: 1.45;
        margin-top: 7px;
    }
    .live-card-details div {
        margin: 3px 0;
    }
    .live-card-action-title {
        color: rgba(255,255,255,0.50);
        font-size: 9px;
        font-weight: 700;
        margin: 7px 0 3px 0;
    }

    /* Tighten Streamlit spacing used inside the compact live cards. */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0 !important;
    }

    /* Recent-match cards use the same compact visual language as live cards. */
    .recent-card-date {
        color: rgba(255,255,255,0.55);
        font-size: 10px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .recent-card-team-link {
        display: block;
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 14px;
        font-weight: 800;
        line-height: 1.25;
        margin: 2px 0;
    }

    .recent-card-team-link:hover {
        color: #c5caff !important;
        text-decoration: underline !important;
    }

    .recent-card-vs {
        color: rgba(255,255,255,0.40);
        font-size: 10px;
        font-weight: 700;
        margin: 2px 0;
    }

    .recent-card-score-box {
        min-height: 72px;
        padding: 10px 6px 8px 6px;
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        text-align: center;
        background: rgba(3,7,15,0.24);
        box-sizing: border-box;
    }

    .recent-card-score-team {
        color: rgba(255,255,255,0.58);
        font-size: 9px;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .recent-card-score {
        color: #ffffff;
        font-size: 19px;
        font-weight: 900;
        line-height: 1.15;
        margin-top: 7px;
    }

    .recent-card-score-label {
        color: rgba(255,255,255,0.42);
        font-size: 8px;
        margin-top: 3px;
    }

    .recent-card-result {
        margin: 9px 0 8px 0;
        padding: 8px 9px;
        border-radius: 9px;
        background: rgba(0, 150, 110, 0.13);
        border: 1px solid rgba(50, 180, 140, 0.16);
        color: rgba(255,255,255,0.72);
        font-size: 9px;
        line-height: 1.35;
    }

    .recent-card-details {
        color: rgba(255,255,255,0.48);
        font-size: 9px;
        line-height: 1.45;
        margin-top: 7px;
    }

    .recent-card-details div {
        margin: 3px 0;
    }

    .recent-card-prediction {
        margin-top: 8px;
        padding: 7px 9px;
        border-radius: 8px;
        background: rgba(90, 130, 255, 0.10);
        border: 1px solid rgba(100, 140, 255, 0.18);
        color: rgba(255,255,255,0.68);
        font-size: 9px;
        line-height: 1.35;
    }

    .hot-chip {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        background: rgba(255, 70, 70, 0.14);
        border: 1px solid rgba(255, 100, 100, 0.30);
    }

    .predict-chip {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        background: rgba(90, 130, 255, 0.12);
        border: 1px solid rgba(100, 140, 255, 0.25);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Session state

st.session_state.setdefault(
    "scorecards_viewed",
    set(),
)

st.session_state.setdefault(
    "predictions",
    {},
)


# Helper functions

def load_named_recent_match_cache():
    """Load individual human-readable recent-match cache files."""
    cache_dir = PROJECT_ROOT / "data" / "api_cache"
    if not cache_dir.exists():
        return []
    matches = []
    seen_ids = set()
    try:
        cache_files = sorted(cache_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return []
    for cache_file in cache_files:
        if (
            cache_file.name.startswith("top player leaderboard_")
            or cache_file.name.startswith("Top_leaderboard_")
        ):
            continue
        try:
            with cache_file.open("r", encoding="utf-8") as file:
                match = json.load(file)
            if not isinstance(match, dict):
                continue
            info = match.get("matchInfo")
            if not isinstance(info, dict):
                continue
            match_id = info.get("matchId")
            if match_id is None or str(match_id) in seen_ids:
                continue
            seen_ids.add(str(match_id))
            matches.append(match)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return matches


def named_recent_cache_response():
    """Build the response structure expected by extract_recent_matches()."""
    matches = load_named_recent_match_cache()
    if not matches:
        return None
    grouped = {}
    for match in matches:
        info = match.get("matchInfo", {})
        match_type = info.get("matchFormat", "Other")
        series_name = info.get("seriesName", "Unknown Series")
        grouped.setdefault((match_type, series_name), []).append(match)
    by_type = {}
    for (match_type, series_name), match_list in grouped.items():
        by_type.setdefault(match_type, []).append({
            "seriesAdWrapper": {
                "seriesName": series_name,
                "matches": match_list,
            }
        })
    return {
        "typeMatches": [
            {"matchType": match_type, "seriesMatches": series_list}
            for match_type, series_list in by_type.items()
        ],
        "_data_source": "cache",
        "_cache_is_fallback": True,
    }




def format_match_date(timestamp):
    if not timestamp:
        return "Date unavailable"

    try:
        timestamp = int(timestamp)

        date = pd.to_datetime(
            timestamp,
            unit="ms",
            errors="coerce",
        )

        if pd.isna(date):
            return "Date unavailable"

        return date.strftime("%d %b %Y")

    except (ValueError, TypeError):
        return "Date unavailable"


def extract_recent_matches(data):
    matches = []

    for type_block in data.get("typeMatches", []):

        match_type = type_block.get(
            "matchType",
            "Other",
        )

        for series_block in type_block.get(
            "seriesMatches",
            [],
        ):

            series_data = series_block.get(
                "seriesAdWrapper",
                {},
            )

            for match_block in series_data.get(
                "matches",
                [],
            ):

                match_info = match_block.get(
                    "matchInfo",
                    {},
                )

                match_score = match_block.get(
                    "matchScore",
                    {},
                )

                team1 = match_info.get(
                    "team1",
                    {},
                )

                team2 = match_info.get(
                    "team2",
                    {},
                )

                venue_info = match_info.get(
                    "venueInfo",
                    {},
                )

                matches.append(
                    {
                        "Series": match_info.get(
                            "seriesName",
                            series_data.get(
                                "seriesName",
                                "Unknown Series",
                            ),
                        ),
                        "Format": match_info.get(
                            "matchFormat",
                            match_type,
                        ),
                        "Match": match_info.get(
                            "matchDesc",
                            "Match",
                        ),
                        "Team 1": team1.get(
                            "teamName",
                            "",
                        ),
                        "Team 1 Short": team1.get(
                            "teamSName",
                            "",
                        ),
                        "Team 2": team2.get(
                            "teamName",
                            "",
                        ),
                        "Team 2 Short": team2.get(
                            "teamSName",
                            "",
                        ),
                        "Date": format_match_date(
                            match_info.get(
                                "startDate"
                            )
                        ),
                        "Venue": venue_info.get(
                            "ground",
                            "",
                        ),
                        "City": venue_info.get(
                            "city",
                            "",
                        ),
                        "Status": match_info.get(
                            "status",
                            "",
                        ),
                        "State": match_info.get(
                            "state",
                            "",
                        ),
                        "State Title": match_info.get(
                            "stateTitle",
                            "",
                        ),
                        "Match ID": match_info.get(
                            "matchId"
                        ),
                        "Score": match_score,
                    }
                )

    return matches


def is_completed_match(status):
    if not status:
        return False

    status_lower = str(status).strip().lower()

    completed_phrases = [
        "won by",
        "match tied",
        "tied",
        "no result",
        "abandoned",
        "cancelled",
        "canceled",
        "match drawn",
        "drawn",
    ]

    return any(
        phrase in status_lower
        for phrase in completed_phrases
    )


def get_latest_innings(team_score):
    if not isinstance(team_score, dict):
        return None

    innings = []

    for key, value in team_score.items():

        if not isinstance(value, dict):
            continue

        if key.lower().startswith("inngs"):
            innings.append(value)

    if not innings:
        return None

    return innings[-1]


def get_team_innings(team_score):
    if not isinstance(team_score, dict):
        return []

    innings = []

    for key, value in team_score.items():

        if not isinstance(value, dict):
            continue

        if key.lower().startswith("inngs"):
            innings.append(value)

    return innings


def format_innings_score(innings):
    if not innings:
        return None

    if "runs" not in innings:
        return None

    runs = innings.get(
        "runs",
        0,
    )

    wickets = innings.get(
        "wickets",
        0,
    )

    overs = innings.get(
        "overs",
        0,
    )

    return f"{runs}/{wickets} ({overs} ov)"


def format_recent_team_score(team_score):
    innings = get_team_innings(
        team_score
    )

    if not innings:
        return "Score unavailable"

    scores = []

    for inning in innings:

        score = format_innings_score(
            inning
        )

        if score:
            scores.append(score)

    if not scores:
        return "Score unavailable"

    return " & ".join(scores)


def get_live_team_score(team_score):
    innings = get_latest_innings(
        team_score
    )

    if not innings:
        return "Score unavailable"

    return format_innings_score(
        innings
    ) or "Score unavailable"


def get_cricbuzz_match_url(match_id):
    """Build the official Cricbuzz live-score URL for a match."""
    if match_id in (None, "", 0):
        return "https://www.cricbuzz.com/cricket-match/live-scores"
    return f"https://www.cricbuzz.com/live-cricket-scores/{match_id}"


def format_recent_compact_score(team_score):
    """Return a compact runs/wickets score for the recent-match card."""
    innings = get_latest_innings(team_score)

    if not innings or "runs" not in innings:
        return "—"

    runs = innings.get("runs", 0)
    wickets = innings.get("wickets", 0)

    return f"{runs}/{wickets}"


def create_batting_dataframe(batsmen):
    rows = []

    for batsman in batsmen:

        rows.append(
            {
                "Batter": batsman.get(
                    "name",
                    "",
                ),
                "Dismissal": batsman.get(
                    "outdec",
                    "",
                ) or "not out",
                "R": batsman.get(
                    "runs",
                    0,
                ),
                "B": batsman.get(
                    "balls",
                    0,
                ),
                "4s": batsman.get(
                    "fours",
                    0,
                ),
                "6s": batsman.get(
                    "sixes",
                    0,
                ),
                "SR": batsman.get(
                    "strkrate",
                    "0",
                ),
            }
        )

    return pd.DataFrame(rows)


def create_bowling_dataframe(bowlers):
    rows = []

    for bowler in bowlers:

        rows.append(
            {
                "Bowler": bowler.get(
                    "name",
                    "",
                ),
                "O": bowler.get(
                    "overs",
                    "0",
                ),
                "M": bowler.get(
                    "maidens",
                    0,
                ),
                "R": bowler.get(
                    "runs",
                    0,
                ),
                "W": bowler.get(
                    "wickets",
                    0,
                ),
                "Econ": bowler.get(
                    "economy",
                    "0",
                ),
            }
        )

    return pd.DataFrame(rows)


def render_innings(innings):

    team_name = innings.get(
        "batteamname",
        "Batting Team",
    )

    score = innings.get(
        "score",
        0,
    )

    wickets = innings.get(
        "wickets",
        0,
    )

    overs = innings.get(
        "overs",
        0,
    )

    run_rate = innings.get(
        "runrate",
        0,
    )

    st.markdown(
        f"## 🏏 {team_name} "
        f"**{score}/{wickets} ({overs} ov)**"
    )

    if run_rate is not None:

        st.caption(
            f"Current Run Rate: {run_rate}"
        )

    st.markdown("### Batting")

    batting_df = create_batting_dataframe(
        innings.get(
            "batsman",
            [],
        )
    )

    if batting_df.empty:

        st.info(
            "No batting data available."
        )

    else:

        st.dataframe(
            batting_df,
            use_container_width=True,
            hide_index=True,
        )

    extras = innings.get(
        "extras",
        {},
    )

    if extras:

        st.markdown("### Extras")

        extras_df = pd.DataFrame(
            [
                {
                    "Byes": extras.get(
                        "byes",
                        0,
                    ),
                    "Leg Byes": extras.get(
                        "legbyes",
                        0,
                    ),
                    "Wides": extras.get(
                        "wides",
                        0,
                    ),
                    "No Balls": extras.get(
                        "noballs",
                        0,
                    ),
                    "Penalty": extras.get(
                        "penalty",
                        0,
                    ),
                    "Total": extras.get(
                        "total",
                        0,
                    ),
                }
            ]
        )

        st.dataframe(
            extras_df,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Bowling")

    bowling_df = create_bowling_dataframe(
        innings.get(
            "bowler",
            [],
        )
    )

    if bowling_df.empty:

        st.info(
            "No bowling data available."
        )

    else:

        st.dataframe(
            bowling_df,
            use_container_width=True,
            hide_index=True,
        )

    fow_data = (
        innings.get(
            "fow",
            {},
        ).get(
            "fow",
            []
        )
    )

    if fow_data:

        st.markdown("### Fall of Wickets")

        fow_rows = []

        for wicket in fow_data:

            fow_rows.append(
                {
                    "Batter": wicket.get(
                        "batsmanname",
                        "",
                    ),
                    "Score": wicket.get(
                        "runs",
                        "",
                    ),
                    "Over": wicket.get(
                        "overnbr",
                        "",
                    ),
                }
            )

        fow_df = pd.DataFrame(
            fow_rows
        )

        st.dataframe(
            fow_df,
            use_container_width=True,
            hide_index=True,
        )

    powerplay_data = (
        innings.get(
            "pp",
            {},
        ).get(
            "powerplay",
            []
        )
    )

    if powerplay_data:

        st.markdown("### Powerplay")

        pp_rows = []

        for powerplay in powerplay_data:

            pp_rows.append(
                {
                    "Type": powerplay.get(
                        "pptype",
                        "",
                    ),
                    "Overs": (
                        f"{powerplay.get('ovrfrom', '')} - "
                        f"{powerplay.get('ovrto', '')}"
                    ),
                    "Runs": powerplay.get(
                        "run",
                        0,
                    ),
                    "Wickets": powerplay.get(
                        "wickets",
                        0,
                    ),
                }
            )

        pp_df = pd.DataFrame(
            pp_rows
        )

        st.dataframe(
            pp_df,
            use_container_width=True,
            hide_index=True,
        )


def render_match_scorecard(scorecard_data):

    innings_list = scorecard_data.get(
        "scorecard",
        []
    )

    if not innings_list:

        st.warning(
            "No detailed scorecard data is "
            "available for this match."
        )

        return

    for index, innings in enumerate(
        innings_list,
        start=1,
    ):

        innings_id = innings.get(
            "inningsid",
            index,
        )

        with st.expander(
            f"Innings {innings_id} — "
            f"{innings.get('batteamname', 'Team')}",
            expanded=True,
        ):

            render_innings(
                innings
            )

    status = scorecard_data.get(
        "status"
    )

    if status:

        st.info(
            f"📌 {status}"
        )


def award_scorecard_xp(match_id):
    """First time a scorecard is opened for a match, grant XP."""

    key = str(match_id)

    if key in st.session_state[
        "scorecards_viewed"
    ]:

        return

    st.session_state[
        "scorecards_viewed"
    ].add(key)

    leveled_up = add_xp(10)

    st.toast(
        "🔍 Scorecard Explorer: +10 XP",
        icon="🧾",
    )

    if leveled_up:
        st.balloons()


# Page introduction

# Profile and XP strip hidden on this page
# Predictions and scorecard rewards remain available in match cards

# Match tabs
#
# Tab setup
# Create tabs before rendering either
# Live or recent content

# Load live data from the cache/API policy
live_data = get_live_matches()
render_sidebar_live_scores(live_data)


tab_live, tab_recent = st.tabs(
    [
        "Live now",
        "Recent Matches",
    ]
)


# Live matches

with tab_live:

    if st.button(
        "🔄 Refresh live scores",
        key="refresh_live_scores",
    ):
        data = get_live_matches(force_refresh=True)
    else:
        data = live_data

    if "error" in data:

        st.warning(
            "Unable to load live matches right now."
        )

    else:

        live_match_count = 0

        matches = data.get(
            "typeMatches",
            []
        )

        for type_block in matches:

            for series in type_block.get(
                "seriesMatches",
                []
            ):

                series_data = series.get(
                    "seriesAdWrapper",
                    {}
                )

                series_name = series_data.get(
                    "seriesName",
                    "Series",
                )

                live_matches = []

                for match_block in series_data.get(
                    "matches",
                    []
                ):

                    info = match_block.get(
                        "matchInfo",
                        {}
                    )

                    status = info.get(
                        "status",
                        "",
                    )

                    if is_completed_match(
                        status
                    ):
                        continue

                    live_matches.append(
                        match_block
                    )

                if not live_matches:
                    continue

                st.markdown(
                    f"#### 🏆 {html.escape(str(series_name))}"
                )

                live_match_count += len(
                    live_matches
                )

                # Live match card layout
                for card_start in range(0, len(live_matches), 2):

                    card_batch = live_matches[card_start:card_start + 2]
                    card_columns = st.columns(2, gap="small")

                    for card_col, match_block in zip(card_columns, card_batch):

                        info = match_block.get(
                            "matchInfo",
                            {}
                        )

                        score = match_block.get(
                            "matchScore",
                            {}
                        )

                        team1_data = info.get(
                            "team1",
                            {}
                        )

                        team2_data = info.get(
                            "team2",
                            {}
                        )

                        team1 = team1_data.get(
                            "teamName",
                            "Team 1",
                        )

                        team2 = team2_data.get(
                            "teamName",
                            "Team 2",
                        )

                        status = info.get(
                            "status",
                            "",
                        )

                        match_id = info.get(
                            "matchId"
                        )

                        match_format = info.get(
                            "matchFormat",
                            "",
                        )

                        match_desc = info.get(
                            "matchDesc",
                            "Match",
                        )

                        match_date = format_match_date(
                            info.get("startDate")
                        )

                        venue_info = info.get(
                            "venueInfo",
                            {}
                        )

                        venue = venue_info.get(
                            "ground",
                            ""
                        )

                        city = venue_info.get(
                            "city",
                            ""
                        )

                        team1_score = score.get(
                            "team1Score",
                            {}
                        )

                        team2_score = score.get(
                            "team2Score",
                            {}
                        )

                        team1_display = get_live_team_score(
                            team1_score
                        )

                        team2_display = get_live_team_score(
                            team2_score
                        )

                        team1_url = get_cricbuzz_match_url(
                            match_id
                        )

                        team2_url = team1_url

                        with card_col:

                            with st.container(
                                border=True
                            ):

                                # Date and live marker
                                st.markdown(
                                    f"""
                                    <div class="live-card-date">
                                        🗓️ {html.escape(str(match_date))}
                                        <span style="float:right;">🏏 🔴 LIVE</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                # Team links
                                st.markdown(
                                    f"""
                                    <a class="live-card-team-link"
                                       href="{team1_url}"
                                       target="_blank">
                                        {html.escape(str(team1))}
                                    </a>
                                    <div class="live-card-vs">VS</div>
                                    <a class="live-card-team-link"
                                       href="{team2_url}"
                                       target="_blank">
                                        {html.escape(str(team2))}
                                    </a>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                # Score boxes
                                score_col1, score_col2 = st.columns(
                                    2,
                                    gap="small",
                                )

                                with score_col1:

                                    st.markdown(
                                        f"""
                                        <div class="live-card-score-box">
                                            <div class="live-card-score-team">
                                                🏏 {html.escape(str(team1))}
                                            </div>
                                            <div class="live-card-score">
                                                {html.escape(str(team1_display))}
                                            </div>
                                            <div class="live-card-score-label">
                                                LIVE SCORE
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                with score_col2:

                                    st.markdown(
                                        f"""
                                        <div class="live-card-score-box">
                                            <div class="live-card-score-team">
                                                🏏 {html.escape(str(team2))}
                                            </div>
                                            <div class="live-card-score">
                                                {html.escape(str(team2_display))}
                                            </div>
                                            <div class="live-card-score-label">
                                                LIVE SCORE
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                # Live status
                                if status:

                                    st.markdown(
                                        f"""
                                        <div class="live-card-status">
                                            🔴 <strong>LIVE</strong><br>
                                            {html.escape(str(status))}
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                # Match details
                                details = []

                                if match_desc:
                                    details.append(
                                        f"🏏 {html.escape(str(match_desc))}"
                                    )

                                if match_format:
                                    details.append(
                                        f"🏏 {html.escape(str(match_format).upper())}"
                                    )

                                if venue and city:
                                    details.append(
                                        f"🏟️ {html.escape(str(venue))}, {html.escape(str(city))}"
                                    )
                                elif venue:
                                    details.append(
                                        f"🏟️ {html.escape(str(venue))}"
                                    )
                                elif city:
                                    details.append(
                                        f"📍 {html.escape(str(city))}"
                                    )

                                if details:

                                    detail_html = "".join(
                                        f"<div>{item}</div>"
                                        for item in details
                                    )

                                    st.markdown(
                                        f"""
                                        <div class="live-card-details">
                                            {detail_html}
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                # Prediction and scorecard
                                if match_id is not None:

                                    pred_key = str(
                                        match_id
                                    )

                                    existing = (
                                        st.session_state[
                                            "predictions"
                                        ].get(
                                            pred_key
                                        )
                                    )

                                    if existing:

                                        st.success(
                                            f"🔮 Prediction: **{existing['team']}**"
                                        )

                                    else:

                                        st.markdown(
                                            '<div class="live-card-action-title">'
                                            '🔮 PREDICT THE WINNER'
                                            '</div>',
                                            unsafe_allow_html=True,
                                        )

                                        pick = st.selectbox(
                                            "Predict the winner",
                                            [
                                                team1,
                                                team2,
                                            ],
                                            key=(
                                                f"pred_select_"
                                                f"{pred_key}"
                                            ),
                                            label_visibility="collapsed",
                                        )

                                        if st.button(
                                            "🔒 Lock Prediction",
                                            key=(
                                                f"pred_btn_"
                                                f"{pred_key}"
                                            ),
                                            use_container_width=True,
                                        ):

                                            st.session_state[
                                                "predictions"
                                            ][
                                                pred_key
                                            ] = {
                                                "team": pick,
                                                "resolved": False,
                                            }

                                            leveled_up = add_xp(
                                                5
                                            )

                                            st.toast(
                                                f"🔮 Prediction locked: "
                                                f"{pick} +5 XP",
                                                icon="🎲",
                                            )

                                            if leveled_up:
                                                st.balloons()

                                            st.rerun()

                                    if st.button(
                                        "🧾 View Scorecard",
                                        key=(
                                            f"scard_"
                                            f"{match_id}"
                                        ),
                                        use_container_width=True,
                                    ):

                                        scorecard = (
                                            get_match_scorecard(
                                                str(match_id)
                                            )
                                        )

                                        if "error" in scorecard:

                                            st.warning(
                                                "Couldn't load the "
                                                f"scorecard: "
                                                f"{scorecard['error']}"
                                            )

                                        else:

                                            award_scorecard_xp(
                                                match_id
                                            )

                                            render_match_scorecard(
                                                scorecard
                                            )

                    st.write("")

        if live_match_count == 0:

            st.info(
                "🏏 No live matches right now."
            )

        else:

            complete_mission(
                "live"
            )

            st.caption(
                f"🔴 {live_match_count} live "
                f"match"
                f"{'es' if live_match_count != 1 else ''} "
                "currently being tracked."
            )


# Recent matches

with tab_recent:

    data = get_recent_matches()

    # Use individual cache files before showing an API error
    if "error" in data:

        cached_recent = named_recent_cache_response()

        if cached_recent is not None:
            data = cached_recent

        else:
            st.info(
                "No recent match data is currently available."
            )
            data = None

    if data is not None and "error" not in data:

        recent_matches = extract_recent_matches(
            data
        )

        if not recent_matches:

            st.info(
                "No recent matches found."
            )

        else:

            # Resolve predictions

            for match in recent_matches:

                mid = (
                    str(match["Match ID"])
                    if match["Match ID"] is not None
                    else None
                )

                pred = (
                    st.session_state[
                        "predictions"
                    ].get(mid)
                    if mid
                    else None
                )

                if pred and not pred.get(
                    "resolved"
                ):

                    status_lower = (
                        match["Status"] or ""
                    ).lower()

                    if "won by" in status_lower:

                        predicted_lower = (
                            pred["team"].lower()
                        )

                        if predicted_lower in status_lower:

                            leveled_up = add_xp(
                                20,
                                coins=5,
                            )

                            st.toast(
                                f"🏆 Correct call! "
                                f"{match['Team 1']} vs "
                                f"{match['Team 2']} — "
                                "+20 XP, +5 coins",
                                icon="🎉",
                            )

                            if leveled_up:
                                st.balloons()

                        else:

                            add_xp(2)

                            st.toast(
                                f"📉 Missed that one — "
                                f"{match['Status']}. "
                                "+2 XP for playing.",
                                icon="🎯",
                            )

                        pred["resolved"] = True


            formats = sorted(
                {
                    match["Format"]
                    for match in recent_matches
                    if match["Format"]
                }
            )

            selected_format = st.selectbox(
                "Filter by format",
                ["All"] + formats,
                key="recent_format",
            )

            filtered_matches = recent_matches

            if selected_format != "All":

                filtered_matches = [
                    match
                    for match in recent_matches
                    if match["Format"]
                    == selected_format
                ]

            # Recent match card layout
            for card_start in range(0, len(filtered_matches), 2):

                card_batch = filtered_matches[
                    card_start:card_start + 2
                ]

                card_columns = st.columns(
                    2,
                    gap="small",
                )

                for card_col, match in zip(
                    card_columns,
                    card_batch,
                ):

                    team1 = match["Team 1"]
                    team2 = match["Team 2"]

                    team1_score = format_recent_compact_score(
                        match["Score"].get(
                            "team1Score",
                            {},
                        )
                    )

                    team2_score = format_recent_compact_score(
                        match["Score"].get(
                            "team2Score",
                            {},
                        )
                    )

                    status = match["Status"]
                    state_title = match["State Title"]

                    venue = match["Venue"]
                    city = match["City"]

                    match_id = match["Match ID"]

                    team1_url = get_cricbuzz_match_url(
                        match_id
                    )
                    team2_url = team1_url

                    with card_col:

                        with st.container(
                            border=True
                        ):

                            # Date and match marker
                            st.markdown(
                                f"""
                                <div class="recent-card-date">
                                    🗓️ {html.escape(str(match["Date"]))}
                                    <span style="float:right;">🏏</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            # Team links.
                            st.markdown(
                                f"""
                                <a class="recent-card-team-link"
                                   href="{team1_url}"
                                   target="_blank">
                                    {html.escape(str(team1))}
                                </a>

                                <div class="recent-card-vs">VS</div>

                                <a class="recent-card-team-link"
                                   href="{team2_url}"
                                   target="_blank">
                                    {html.escape(str(team2))}
                                </a>
                                """,
                                unsafe_allow_html=True,
                            )

                            # Score boxes
                            score_col1, score_col2 = st.columns(
                                2,
                                gap="small",
                            )

                            with score_col1:

                                st.markdown(
                                    f"""
                                    <div class="recent-card-score-box">
                                        <div class="recent-card-score-team">
                                            🏏 {html.escape(str(team1))}
                                        </div>
                                        <div class="recent-card-score">
                                            {html.escape(str(team1_score))}
                                        </div>
                                        <div class="recent-card-score-label">
                                            SCORE
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            with score_col2:

                                st.markdown(
                                    f"""
                                    <div class="recent-card-score-box">
                                        <div class="recent-card-score-team">
                                            🏏 {html.escape(str(team2))}
                                        </div>
                                        <div class="recent-card-score">
                                            {html.escape(str(team2_score))}
                                        </div>
                                        <div class="recent-card-score-label">
                                            SCORE
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            # Match result
                            result_text = status or state_title

                            if result_text:

                                result_icon = (
                                    "🏆"
                                    if status
                                    else "📌"
                                )

                                st.markdown(
                                    f"""
                                    <div class="recent-card-result">
                                        {result_icon}
                                        <strong>
                                            {html.escape(str(result_text))}
                                        </strong>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            # Match details.
                            details = []

                            if match["Format"]:
                                details.append(
                                    f"🏏 {html.escape(str(match['Format']).upper())}"
                                )

                            if venue and city:
                                details.append(
                                    f"🏟️ {html.escape(str(venue))}, "
                                    f"{html.escape(str(city))}"
                                )
                            elif venue:
                                details.append(
                                    f"🏟️ {html.escape(str(venue))}"
                                )
                            elif city:
                                details.append(
                                    f"📍 {html.escape(str(city))}"
                                )

                            if details:

                                detail_html = "".join(
                                    f"<div>{item}</div>"
                                    for item in details
                                )

                                st.markdown(
                                    f"""
                                    <div class="recent-card-details">
                                        {detail_html}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            # Prediction result
                            pred = st.session_state[
                                "predictions"
                            ].get(
                                str(match_id)
                                if match_id is not None
                                else None
                            )

                            if pred:

                                status_lower = (
                                    status or ""
                                ).lower()

                                is_correct = (
                                    "won by" in status_lower
                                    and pred["team"].lower()
                                    in status_lower
                                )

                                if is_correct:

                                    prediction_text = (
                                        f"🔮 You picked "
                                        f"<strong>{html.escape(str(pred['team']))}</strong>"
                                        f" — Correct"
                                    )

                                else:

                                    prediction_text = (
                                        f"🔮 You picked "
                                        f"<strong>{html.escape(str(pred['team']))}</strong>"
                                    )

                                st.markdown(
                                    f"""
                                    <div class="recent-card-prediction">
                                        {prediction_text}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            # Scorecard
                            if st.button(
                                "🧾 View Scorecard",
                                key=(
                                    f"recent_scard_"
                                    f"{match_id}"
                                ),
                                use_container_width=True,
                            ):

                                scorecard = (
                                    get_match_scorecard(
                                        str(match_id)
                                    )
                                )

                                if "error" in scorecard:

                                    st.warning(
                                        "Couldn't load the "
                                        f"scorecard: "
                                        f"{scorecard['error']}"
                                    )

                                else:

                                    award_scorecard_xp(
                                        match_id
                                    )

                                    render_match_scorecard(
                                        scorecard
                                    )




st.caption(
    "Live data refreshes every 8 hours unless manually refreshed. "
    "Recent-match data refreshes every 24 hours. "
    "Player rankings refresh every 30 days. "
    "A persistent fallback cache is retained for up to 30 days. "
    "Predictions and scorecard activity are tracked per browser session."
)
