import html
import re
import sys
import json
import sqlite3
from pathlib import Path
from textwrap import dedent

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
    get_match_commentaries,
    get_team_results,
    get_venue_matches,
    get_venue_stats,
    get_series_venues,
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


# Session cache for on-demand player analytics scorecards
st.session_state.setdefault("analytics_scorecards", {})


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

    /* Keep the Cricbuzz LiveStats footer branding pinned to the bottom. */
    [data-testid="stSidebar"]::after {
        content: "CRICBUZZ LIVESTATS";

        position: fixed;
        left: 20px;
        bottom: 14px;

        width: 232px;
        box-sizing: border-box;

        padding-top: 14px;

        border-top: 1px solid rgba(255,255,255,0.09);

        color: rgba(255,255,255,0.28);

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 1.5px;
        pointer-events: none;
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
        margin: 0 4px 0 4px;
        padding-top: 0;
        border-top: none;
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





















    .live-commentary-panel {
        margin-top: 9px;
        padding: 9px 10px;
        border-radius: 9px;
        background: rgba(110, 130, 255, 0.07);
        border: 1px solid rgba(120, 140, 255, 0.18);
    }

    .live-commentary-heading {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 7px;
        color: rgba(255,255,255,0.86);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 0.7px;
    }

    .live-commentary-source {
        color: rgba(170,180,255,0.78);
        font-size: 7px;
        letter-spacing: 0.7px;
    }

    .live-commentary-item {
        padding: 7px 0;
        border-top: 1px solid rgba(255,255,255,0.06);
    }

    .live-commentary-meta {
        display: flex;
        align-items: center;
        gap: 7px;
        margin-bottom: 3px;
        color: rgba(255,255,255,0.38);
        font-size: 7px;
        font-weight: 800;
    }

    .live-commentary-event {
        color: rgba(255, 194, 92, 0.90);
        font-size: 7px;
        font-weight: 900;
    }

    .live-commentary-text {
        color: rgba(255,255,255,0.74);
        font-size: 9px;
        line-height: 1.42;
    }

    .live-analytics-panel {
        min-height: 100%;
    }

    div[data-testid="stTabs"] button {
        font-size: 11px !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Scorecard layout

st.markdown(
    """
    <style>
    .scorecard-header {
        margin: 10px 0 14px 0;
        padding: 14px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.035);
    }

    .scorecard-header-label {
        color: rgba(255,255,255,0.45);
        font-size: 9px;
        font-weight: 900;
        letter-spacing: 1.1px;
        margin-bottom: 10px;
    }

    .scorecard-header-teams {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }

    .scorecard-team-block {
        min-width: 0;
        padding: 11px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(3,7,15,0.24);
    }

    .scorecard-team-name {
        color: rgba(255,255,255,0.70);
        font-size: 11px;
        font-weight: 800;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .scorecard-team-score {
        margin-top: 6px;
        color: #ffffff;
        font-size: 19px;
        font-weight: 900;
        line-height: 1.25;
    }

    .scorecard-innings-title {
        display: flex;
        align-items: baseline;
        gap: 7px;
        margin: 2px 0 8px 0;
    }

    .scorecard-innings-title span {
        color: rgba(255,255,255,0.82);
        font-size: 15px;
        font-weight: 800;
        flex: 1;
    }

    .scorecard-innings-title strong {
        color: #ffffff;
        font-size: 18px;
        font-weight: 900;
    }

    .scorecard-innings-title small {
        color: rgba(255,255,255,0.42);
        font-size: 9px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Commentary helpers

def _clean_commentary_text(value):
    """Clean Cricbuzz commentary formatting markers and HTML."""
    if value in (None, ""):
        return ""

    text = str(value)
    text = text.replace("\\u003c", "<").replace("\\u003e", ">")
    text = re.sub(r"[A-Z]\d+\$", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _commentary_items(payload):
    """Extract commentary from the actual Cricbuzz /comm response."""
    if not isinstance(payload, dict):
        return []

    raw_items = []

    # Current Cricbuzz structure:
    # comwrapper -> commentary -> commtxt / overnum / inningsid / ballnbr / eventtype

    comwrapper = payload.get("comwrapper", [])

    if isinstance(comwrapper, list):
        for wrapper in comwrapper:
            if not isinstance(wrapper, dict):
                continue

            commentary = wrapper.get("commentary")

            if isinstance(commentary, dict):
                raw_items.append(commentary)

    # Keep support for the alternate commentaryList response shape.

    commentary_list = payload.get("commentaryList")

    if isinstance(commentary_list, list):
        raw_items.extend(
            item for item in commentary_list
            if isinstance(item, dict)
        )

    result = []
    seen = set()

    for item in raw_items:
        text = _clean_commentary_text(
            item.get("commtxt")
            or item.get("commText")
            or item.get("commentary")
            or item.get("text")
            or ""
        )

        if not text:
            continue

        # Skip internal Cricbuzz formatting-marker-only records.
        if len(text) <= 12 and text.endswith("$"):
            continue

        timestamp = item.get("timestamp")

        ball = (
            item.get("ballnbr")
            if item.get("ballnbr") is not None
            else item.get("ballNbr")
        )

        over = (
            item.get("overnum")
            if item.get("overnum") is not None
            else item.get("overNumber")
        )

        event = (
            item.get("eventtype")
            if item.get("eventtype") is not None
            else item.get("event")
        )

        if isinstance(event, list):
            event = ", ".join(
                str(part)
                for part in event
                if str(part).strip().lower() not in {"none", "all"}
            )

        team = (
            item.get("battingteamname")
            or item.get("batTeamName")
            or item.get("teamName")
            or ""
        )

        key = (
            str(timestamp or ""),
            str(ball or ""),
            str(over or ""),
            text,
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(
            {
                "text": text,
                "timestamp": timestamp,
                "ball": ball,
                "over": over,
                "event": event or "",
                "team": team,
                "innings_id": (
                    item.get("inningsid")
                    if item.get("inningsid") is not None
                    else item.get("inningsId")
                ),
            }
        )

    return result


def _format_commentary_time(timestamp):
    """Format an API timestamp for the commentary card."""
    if timestamp in (None, ""):
        return ""

    try:
        value = pd.to_datetime(
            int(timestamp),
            unit="ms",
            errors="coerce",
        )

        if pd.isna(value):
            return ""

        return value.strftime("%H:%M:%S")
    except (TypeError, ValueError, OverflowError):
        return ""


def render_commentary_section(match_id, team1, team2):
    """Render on-demand commentary, bypassing cache only on explicit button clicks."""
    if match_id in (None, ""):
        return

    session_key = f"commentary_loaded_{match_id}"

    with st.expander("🎙️ Live Commentary", expanded=False):
        st.caption(
            "Ball-by-ball commentary • persistent cache • refreshes from API only when requested"
        )

        load_col, refresh_col = st.columns([3, 1], gap="small")

        with load_col:
            load_commentary = st.button(
                "🎙️ Load commentary",
                key=f"commentary_load_{match_id}",
                use_container_width=True,
            )

        with refresh_col:
            refresh_commentary = st.button(
                "↻ Refresh",
                key=f"commentary_refresh_{match_id}",
                use_container_width=True,
            )

        if load_commentary or refresh_commentary:
            st.session_state[session_key] = True

        if not st.session_state.get(session_key):
            st.caption(
                "Commentary is loaded only when requested to avoid unnecessary API calls."
            )
            return

        # Load commentary from the persistent cache on normal reruns.
        # Only an explicit Load or Refresh click bypasses that cache.
        commentary = get_match_commentaries(
            str(match_id),
            force_refresh=(
                load_commentary or refresh_commentary
            ),
        )

        if not isinstance(commentary, dict) or "error" in commentary:
            error_text = (
                commentary.get("error", "Commentary is unavailable.")
                if isinstance(commentary, dict)
                else "Commentary is unavailable."
            )
            st.warning(f"🎙️ {error_text}")
            return

        items = _commentary_items(commentary)

        if not items:
            st.info(
                "No ball-by-ball commentary is currently available for this match."
            )
            return

        source = commentary.get("_data_source", "cache")
        age = commentary.get("_cache_age_seconds")

        if source == "api":
            source_label = "LIVE API"
        elif source == "fallback":
            source_label = "STALE CACHE"
        else:
            source_label = "CACHE"

        if age is None:
            cache_meta = source_label
        else:
            age_seconds = max(0, int(age))
            if age_seconds < 60:
                cache_meta = f"{source_label} • {age_seconds}s old"
            else:
                cache_meta = f"{source_label} • {age_seconds // 60}m old"

        st.markdown(f"**🎙️ Latest Commentary** · `{cache_meta}`")

        for item in items[:10]:
            over = item.get("over")
            ball = item.get("ball")
            timestamp = _format_commentary_time(item.get("timestamp"))
            event = str(item.get("event", "")).strip()
            if event.lower() in {"none", "all"}:
                event = ""

            meta_parts = []
            if over not in (None, ""):
                meta_parts.append(f"Over {over}")
            elif ball not in (None, ""):
                meta_parts.append(f"Ball {ball}")
            if timestamp:
                meta_parts.append(timestamp)

            meta_text = " • ".join(meta_parts)
            if event:
                meta_text = f"{meta_text} • {event}" if meta_text else event

            with st.container(border=True):
                if meta_text:
                    st.caption(meta_text)
                st.write(item["text"])

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


def normalize_history_name(value):
    """Normalize player names for matching API names to database names."""
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def _get_history_connection():
    """Open the project SQLite database for read-only analytics."""
    db_path = PROJECT_ROOT / "data" / "cricbuzz_livestats.db"

    if not db_path.exists():
        return None

    try:
        return sqlite3.connect(
            f"file:{db_path.as_posix()}?mode=ro",
            uri=True,
        )
    except sqlite3.Error:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def get_historical_match_data():
    """Load the three-year completed match history from the database."""
    conn = _get_history_connection()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                m.match_id,
                m.team1,
                m.team2,
                m.match_date,
                m.match_type,
                m.winner,
                m.victory_margin,
                m.victory_type,
                m.status,
                m.result_text,
                v.venue_name,
                v.city,
                v.country
            FROM matches m
            LEFT JOIN venues v
                ON v.venue_id = m.venue_id
            WHERE date(m.match_date) >= date('now', '-3 years')
              AND m.team1 IS NOT NULL
              AND m.team2 IS NOT NULL
            ORDER BY date(m.match_date) DESC, m.match_id DESC
        """

        history = pd.read_sql_query(query, conn)
        history["match_date"] = pd.to_datetime(
            history["match_date"],
            errors="coerce",
        )
        return history

    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()

    finally:
        conn.close()


@st.cache_data(ttl=900, show_spinner=False)
def get_historical_player_innings():
    """Load three-year batting history from Q23 plus legacy innings data."""
    conn = _get_history_connection()

    if conn is None:
        return pd.DataFrame()

    try:
        q23_query = """
            SELECT
                id AS history_id,
                player_id,
                player_name,
                real_name,
                format,
                runs_scored,
                balls_faced,
                fours,
                sixes,
                strike_rate,
                batting_position,
                innings_no,
                dismissal,
                opposition,
                ground,
                match_date
            FROM Q23_batting_innings_SR
            WHERE date(match_date) >= date('now', '-3 years')
              AND COALESCE(runs_scored, 0) >= 0
        """

        q23 = pd.read_sql_query(q23_query, conn)

        # Q23 contains the most complete recent-form history. A small number
        # of established players are also present in innings_scores but not
        # in Q23, so add only those missing player IDs as a fallback source.
        q23_player_ids = set(
            pd.to_numeric(q23.get("player_id", pd.Series(dtype="int64")), errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )

        legacy_query = """
            SELECT
                i.id AS history_id,
                i.player_id,
                p.player_name,
                p.player_name AS real_name,
                COALESCE(m.match_type, '') AS format,
                i.runs_scored,
                i.balls_faced,
                i.fours,
                i.sixes,
                i.strike_rate,
                i.batting_position,
                i.innings_no,
                '' AS dismissal,
                CASE
                    WHEN m.team1 = p.player_name THEN m.team2
                    ELSE m.team1
                END AS opposition,
                v.venue_name AS ground,
                i.match_date
            FROM innings_scores i
            JOIN players p
                ON p.player_id = i.player_id
            LEFT JOIN matches m
                ON m.match_id = i.match_id
            LEFT JOIN venues v
                ON v.venue_id = m.venue_id
            WHERE date(i.match_date) >= date('now', '-3 years')
              AND COALESCE(i.runs_scored, 0) >= 0
        """

        legacy = pd.read_sql_query(legacy_query, conn)
        if q23_player_ids and not legacy.empty:
            legacy_ids = pd.to_numeric(
                legacy["player_id"],
                errors="coerce",
            )
            legacy = legacy[~legacy_ids.isin(q23_player_ids)].copy()

        history = pd.concat(
            [q23, legacy],
            ignore_index=True,
            sort=False,
        )

        if history.empty:
            return history

        history["match_date"] = pd.to_datetime(
            history["match_date"],
            errors="coerce",
        )
        history["display_name"] = (
            history["real_name"]
            .fillna(history["player_name"])
            .fillna("")
            .astype(str)
            .str.strip()
        )
        history["format"] = history["format"].fillna("").astype(str)
        return history

    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()

    finally:
        conn.close()

def _team_match_name_key(value):
    """Normalize a team or venue name for historical matching."""
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", " ", text)

    return re.sub(r"\s+", " ", text).strip()


def _same_team(left, right):
    return (
        bool(_team_match_name_key(left))
        and _team_match_name_key(left) == _team_match_name_key(right)
    )


def _completed_history(history):
    """Return matches that represent completed/decided historical games."""
    if history.empty:
        return history.copy()

    result = history.copy()
    status_text = (
        result["status"].fillna("").astype(str).str.lower()
        + " "
        + result["result_text"].fillna("").astype(str).str.lower()
    )

    no_result_mask = status_text.str.contains(
        r"no result|abandoned|cancelled|canceled",
        regex=True,
        na=False,
    )

    return result.loc[~no_result_mask].copy()


def get_h2h_analytics(team1, team2, match_format=None):
    """Calculate three-year head-to-head results from matches."""
    history = get_historical_match_data()

    empty = {
        "matches": pd.DataFrame(),
        "total": 0,
        "team1_wins": 0,
        "team2_wins": 0,
        "ties": 0,
        "no_results": 0,
    }

    if history.empty:
        return empty

    team1_key = _team_match_name_key(team1)
    team2_key = _team_match_name_key(team2)

    mask = (
        (
            history["team1"].map(_team_match_name_key).eq(team1_key)
            & history["team2"].map(_team_match_name_key).eq(team2_key)
        )
        | (
            history["team1"].map(_team_match_name_key).eq(team2_key)
            & history["team2"].map(_team_match_name_key).eq(team1_key)
        )
    )

    all_h2h = history.loc[mask].copy()

    if match_format and not all_h2h.empty:
        fmt = str(match_format).strip().lower()
        format_h2h = all_h2h[
            all_h2h["match_type"]
            .fillna("")
            .astype(str)
            .str.lower()
            .eq(fmt)
        ]

        # Prefer the same format when available, otherwise retain all H2H.
        h2h = format_h2h if not format_h2h.empty else all_h2h
    else:
        h2h = all_h2h

    if h2h.empty:
        return empty

    no_result_mask = (
        h2h["status"].fillna("").astype(str).str.lower()
        .str.contains(
            r"no result|abandoned|cancelled|canceled",
            regex=True,
            na=False,
        )
        | h2h["result_text"].fillna("").astype(str).str.lower()
        .str.contains(
            r"no result|abandoned|cancelled|canceled",
            regex=True,
            na=False,
        )
    )

    team1_wins = int(
        h2h["winner"].fillna("").map(
            lambda x: _same_team(x, team1)
        ).sum()
    )
    team2_wins = int(
        h2h["winner"].fillna("").map(
            lambda x: _same_team(x, team2)
        ).sum()
    )

    ties = int(
        (
            h2h["winner"].fillna("").astype(str).str.strip().eq("")
            & ~no_result_mask
        ).sum()
    )

    return {
        "matches": h2h.sort_values(
            "match_date",
            ascending=False,
            na_position="last",
        ),
        "total": int(len(h2h)),
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "ties": ties,
        "no_results": int(no_result_mask.sum()),
    }


def get_team_recent_form(team, history, match_format=None, limit=10):
    """Calculate recent three-year team form for prediction context."""
    if history.empty or not team:
        return {
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "no_results": 0,
            "win_pct": 0.0,
            "recent": pd.DataFrame(),
        }

    team_key = _team_match_name_key(team)

    team_history = history[
        history["team1"].map(_team_match_name_key).eq(team_key)
        | history["team2"].map(_team_match_name_key).eq(team_key)
    ].copy()

    if match_format and not team_history.empty:
        fmt = str(match_format).strip().lower()
        same_format = team_history[
            team_history["match_type"]
            .fillna("")
            .astype(str)
            .str.lower()
            .eq(fmt)
        ]
        if len(same_format) >= 3:
            team_history = same_format

    team_history = team_history.sort_values(
        "match_date",
        ascending=False,
        na_position="last",
    ).head(limit)

    if team_history.empty:
        return {
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "no_results": 0,
            "win_pct": 0.0,
            "recent": team_history,
        }

    result_text = (
        team_history["status"].fillna("").astype(str).str.lower()
        + " "
        + team_history["result_text"].fillna("").astype(str).str.lower()
    )

    no_result = result_text.str.contains(
        r"no result|abandoned|cancelled|canceled",
        regex=True,
        na=False,
    )

    wins = team_history["winner"].fillna("").map(
        lambda x: _same_team(x, team)
    )

    decided = (~no_result) & team_history["winner"].fillna("").astype(str).str.strip().ne("")
    losses = decided & ~wins

    decided_count = int(decided.sum())

    return {
        "matches": int(len(team_history)),
        "wins": int(wins.sum()),
        "losses": int(losses.sum()),
        "no_results": int(no_result.sum()),
        "win_pct": round(
            100 * float(wins.sum()) / decided_count,
            1,
        ) if decided_count else 0.0,
        "recent": team_history,
    }


def _player_name_key(value):
    """Normalize a player name for robust full-name/initial matching."""
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def _player_tokens(value):
    if value is None:
        return []
    return [
        token
        for token in re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).split()
        if token
    ]


def _match_player_name(player_name, history):
    """Match an API scorecard name to Q23 real_name/player_name safely."""
    if history.empty or not player_name:
        return None

    target_key = _player_name_key(player_name)

    candidates = history[
        history["display_name"].map(_player_name_key).eq(target_key)
        | history["real_name"].fillna("").map(_player_name_key).eq(target_key)
        | history["player_name"].fillna("").map(_player_name_key).eq(target_key)
    ]

    if not candidates.empty:
        return candidates.iloc[0]["display_name"]

    target_tokens = _player_tokens(player_name)
    if not target_tokens:
        return None

    target_last = target_tokens[-1]
    target_initial = target_tokens[0][0]

    unique_players = history[
        ["display_name", "real_name", "player_name"]
    ].drop_duplicates()

    matches = []
    for _, row in unique_players.iterrows():
        names = [
            row.get("display_name", ""),
            row.get("real_name", ""),
            row.get("player_name", ""),
        ]
        for candidate_name in names:
            tokens = _player_tokens(candidate_name)
            if not tokens or tokens[-1] != target_last:
                continue

            if tokens[0][0] == target_initial:
                matches.append(row.get("display_name", candidate_name))
                break

    matches = list(dict.fromkeys(matches))
    return matches[0] if len(matches) == 1 else None


def _filter_player_format(player_df, match_format):
    """Prefer the current match format while retaining a safe fallback."""
    if not match_format or player_df.empty:
        return player_df

    fmt = str(match_format).strip().lower()
    if fmt == "t20":
        accepted = {"t20", "t20i", "it20"}
    elif fmt == "odi":
        accepted = {"odi", "odm"}
    elif fmt == "test":
        accepted = {"test"}
    else:
        accepted = {fmt}

    filtered = player_df[
        player_df["format"].str.strip().str.lower().isin(accepted)
    ].copy()

    return filtered if len(filtered) >= 3 else player_df


def get_player_form_analytics(player_name, history, match_format=None):
    """Calculate recent batting form and momentum from Q23 history."""
    matched_name = _match_player_name(player_name, history)

    if matched_name is None:
        return None

    player_df = history[
        history["display_name"].eq(matched_name)
    ].copy()

    if player_df.empty:
        return None

    player_df = _filter_player_format(player_df, match_format)

    player_df["runs_scored"] = pd.to_numeric(
        player_df["runs_scored"],
        errors="coerce",
    ).fillna(0)
    player_df["balls_faced"] = pd.to_numeric(
        player_df["balls_faced"],
        errors="coerce",
    ).fillna(0)
    player_df["strike_rate"] = pd.to_numeric(
        player_df["strike_rate"],
        errors="coerce",
    )

    player_df = player_df.sort_values(
        ["match_date", "history_id"],
        ascending=False,
        na_position="last",
    ).drop_duplicates(
        subset=["match_date", "innings_no"],
        keep="first",
    ).head(10).copy()

    if player_df.empty:
        return None

    recent5 = player_df.head(5)
    previous5 = player_df.iloc[5:10]

    avg_last5 = float(recent5["runs_scored"].mean())
    avg_last10 = float(player_df["runs_scored"].mean())

    sr_last5_values = recent5["strike_rate"].dropna()
    sr_last10_values = player_df["strike_rate"].dropna()

    sr_last5 = float(sr_last5_values.mean()) if not sr_last5_values.empty else 0.0
    sr_last10 = float(sr_last10_values.mean()) if not sr_last10_values.empty else 0.0

    previous_avg = (
        float(previous5["runs_scored"].mean())
        if not previous5.empty
        else avg_last5
    )

    momentum_delta = avg_last5 - previous_avg
    fifty_plus = int((player_df["runs_scored"] >= 50).sum())
    ducks = int((player_df["runs_scored"] == 0).sum())

    if avg_last5 >= 45 and momentum_delta >= 0:
        form = "🔥 Excellent"
    elif avg_last5 >= 30 or momentum_delta >= 8:
        form = "⚡ Good"
    elif avg_last5 >= 15:
        form = "📈 Average"
    else:
        form = "📉 Needs a lift"

    momentum_score = max(
        0.0,
        min(
            100.0,
            50.0
            + (avg_last5 - 25.0) * 1.2
            + momentum_delta * 1.5
            + min(fifty_plus, 3) * 4.0
            - min(ducks, 3) * 3.0,
        ),
    )

    return {
        "player": matched_name,
        "recent": player_df,
        "matches": int(len(player_df)),
        "avg_last5": avg_last5,
        "avg_last10": avg_last10,
        "sr_last5": sr_last5,
        "sr_last10": sr_last10,
        "momentum_delta": momentum_delta,
        "momentum_score": momentum_score,
        "fifty_plus": fifty_plus,
        "ducks": ducks,
        "form": form,
    }

def get_venue_analytics(team1, team2, venue, city=None, match_format=None):
    """Calculate three-year team performance at the current venue."""
    history = get_historical_match_data()

    if history.empty or not venue:
        return pd.DataFrame()

    venue_key = _team_match_name_key(venue)
    city_key = _team_match_name_key(city)

    venue_mask = history["venue_name"].fillna("").map(
        _team_match_name_key
    ).eq(venue_key)

    if city_key:
        same_city = history["city"].fillna("").map(
            _team_match_name_key
        ).eq(city_key)

        if same_city.any():
            venue_mask &= same_city

    venue_df = history.loc[venue_mask].copy()

    if match_format and not venue_df.empty:
        fmt = str(match_format).strip().lower()
        same_format = venue_df[
            venue_df["match_type"]
            .fillna("")
            .astype(str)
            .str.lower()
            .eq(fmt)
        ]
        if len(same_format) >= 2:
            venue_df = same_format

    if venue_df.empty:
        return pd.DataFrame()

    rows = []

    for team in (team1, team2):
        team_matches = venue_df[
            venue_df["team1"].map(lambda x: _same_team(x, team))
            | venue_df["team2"].map(lambda x: _same_team(x, team))
        ].copy()

        if team_matches.empty:
            rows.append(
                {
                    "Team": team,
                    "Matches": 0,
                    "Wins": 0,
                    "Win %": 0.0,
                    "Avg Victory Margin": 0.0,
                }
            )
            continue

        wins_mask = team_matches["winner"].fillna("").map(
            lambda x: _same_team(x, team)
        )

        margins = pd.to_numeric(
            team_matches.loc[wins_mask, "victory_margin"],
            errors="coerce",
        ).dropna()

        rows.append(
            {
                "Team": team,
                "Matches": int(len(team_matches)),
                "Wins": int(wins_mask.sum()),
                "Win %": round(
                    100 * float(wins_mask.sum()) / len(team_matches),
                    1,
                ),
                "Avg Victory Margin": round(
                    float(margins.mean()),
                    1,
                ) if not margins.empty else 0.0,
            }
        )

    return pd.DataFrame(rows)


def get_historical_prediction_context(team1, team2, match_format=None, venue=None, city=None):
    """
    Build a transparent historical probability indicator.

    This is a database-derived analytical estimate, not bookmaker odds
    and not a betting recommendation.
    """
    history = get_historical_match_data()

    if history.empty:
        return {
            "team1": team1,
            "team2": team2,
            "prob1": 50.0,
            "prob2": 50.0,
            "fair_odds1": 2.0,
            "fair_odds2": 2.0,
            "h2h": get_h2h_analytics(team1, team2, match_format),
            "form1": get_team_recent_form(team1, history, match_format),
            "form2": get_team_recent_form(team2, history, match_format),
            "venue": pd.DataFrame(),
        }

    h2h = get_h2h_analytics(team1, team2, match_format)
    form1 = get_team_recent_form(team1, history, match_format, 10)
    form2 = get_team_recent_form(team2, history, match_format, 10)
    venue_df = get_venue_analytics(
        team1,
        team2,
        venue,
        city,
        match_format,
    )

    # Start from a neutral prior.
    components1 = [50.0]
    components2 = [50.0]
    weights = [0.20]

    # H2H carries weight only when there is a meaningful sample.
    h2h_decided = h2h["team1_wins"] + h2h["team2_wins"]
    if h2h_decided >= 2:
        components1.append(
            100.0 * h2h["team1_wins"] / h2h_decided
        )
        components2.append(
            100.0 * h2h["team2_wins"] / h2h_decided
        )
        weights.append(0.30)

    # Recent team form.
    if form1["matches"] >= 3 and form2["matches"] >= 3:
        components1.append(form1["win_pct"])
        components2.append(form2["win_pct"])
        weights.append(0.35)

    # Venue performance.
    if not venue_df.empty:
        venue1 = float(
            venue_df.loc[
                venue_df["Team"].map(_team_match_name_key).eq(
                    _team_match_name_key(team1)
                ),
                "Win %",
            ].iloc[0]
        ) if not venue_df[
            venue_df["Team"].map(_team_match_name_key).eq(
                _team_match_name_key(team1)
            )
        ].empty else 0.0

        venue2 = float(
            venue_df.loc[
                venue_df["Team"].map(_team_match_name_key).eq(
                    _team_match_name_key(team2)
                ),
                "Win %",
            ].iloc[0]
        ) if not venue_df[
            venue_df["Team"].map(_team_match_name_key).eq(
                _team_match_name_key(team2)
            )
        ].empty else 0.0

        if venue1 + venue2 > 0:
            venue_total = venue1 + venue2
            components1.append(100.0 * venue1 / venue_total)
            components2.append(100.0 * venue2 / venue_total)
            weights.append(0.15)

    # Weighted average, then normalize to 100%.
    prob1 = sum(value * weight for value, weight in zip(components1, weights)) / sum(weights)
    prob2 = sum(value * weight for value, weight in zip(components2, weights)) / sum(weights)

    total_prob = prob1 + prob2
    if total_prob > 0:
        prob1 = 100.0 * prob1 / total_prob
        prob2 = 100.0 * prob2 / total_prob

    return {
        "team1": team1,
        "team2": team2,
        "prob1": round(prob1, 1),
        "prob2": round(prob2, 1),
        "fair_odds1": round(100.0 / prob1, 2) if prob1 > 0 else None,
        "fair_odds2": round(100.0 / prob2, 2) if prob2 > 0 else None,
        "h2h": h2h,
        "form1": form1,
        "form2": form2,
        "venue": venue_df,
    }


def _team_player_history(team, history_matches, player_history, match_format=None):
    """
    Return batting history for players associated with a team's recent
    limited-overs matches.

    For T20/ODI-style scorecards, innings 1/2 map to match team1/team2.
    """
    if history_matches.empty or player_history.empty:
        return pd.DataFrame()

    team_key = _team_match_name_key(team)

    team_matches = history_matches[
        history_matches["team1"].map(_team_match_name_key).eq(team_key)
        | history_matches["team2"].map(_team_match_name_key).eq(team_key)
    ].copy()

    if match_format:
        fmt = str(match_format).strip().lower()
        same_format = team_matches[
            team_matches["match_type"]
            .fillna("")
            .astype(str)
            .str.lower()
            .eq(fmt)
        ]
        if len(same_format) >= 3:
            team_matches = same_format

    limited = team_matches[
        team_matches["match_type"].fillna("").astype(str).str.upper().isin(
            ["T20", "IT20", "ODI", "ODM"]
        )
    ].copy()

    if limited.empty:
        return pd.DataFrame()

    recent_ids = set(
        limited.sort_values("match_date", ascending=False)
        .head(15)["match_id"].astype(int)
    )

    innings = player_history[
        player_history["match_id"].isin(recent_ids)
        & player_history["innings_no"].isin([1, 2])
    ].copy()

    if innings.empty:
        return pd.DataFrame()

    team_by_innings = {}

    for _, row in limited[limited["match_id"].isin(recent_ids)].iterrows():
        team_by_innings[(int(row["match_id"]), 1)] = row["team1"]
        team_by_innings[(int(row["match_id"]), 2)] = row["team2"]

    innings["team"] = [
        team_by_innings.get(
            (int(match_id), int(innings_no)),
            "",
        )
        for match_id, innings_no in zip(
            innings["match_id"],
            innings["innings_no"],
        )
    ]

    innings = innings[
        innings["team"].map(_team_match_name_key).eq(team_key)
    ].copy()

    return innings


def get_pre_match_player_analysis(player_names, match_format=None, limit=5):
    """Rank current scorecard players using three-year Q23 batting history."""
    history = get_historical_player_innings()

    if history.empty or not player_names:
        return pd.DataFrame()

    rows = []
    seen = set()

    for scorecard_name in player_names:
        matched = _match_player_name(scorecard_name, history)
        if matched is None or matched in seen:
            continue

        seen.add(matched)
        player_df = history[history["display_name"].eq(matched)].copy()
        player_df = _filter_player_format(player_df, match_format)
        player_df = player_df.sort_values(
            ["match_date", "history_id"],
            ascending=False,
            na_position="last",
        ).head(10)

        if player_df.empty:
            continue

        runs = pd.to_numeric(player_df["runs_scored"], errors="coerce").fillna(0)
        sr = pd.to_numeric(player_df["strike_rate"], errors="coerce")

        rows.append(
            {
                "player_name": matched,
                "Innings": int(len(player_df)),
                "Runs": int(runs.sum()),
                "Avg": round(float(runs.mean()), 1),
                "SR": round(float(sr.dropna().mean()), 1) if not sr.dropna().empty else 0.0,
                "Fifties": int((runs >= 50).sum()),
                "Momentum": round(
                    float(runs.head(5).mean() - runs.iloc[5:10].mean())
                    if len(runs.iloc[5:10]) > 0
                    else 0.0,
                    1,
                ),
            }
        )

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    return result.sort_values(
        ["Avg", "Runs"],
        ascending=False,
    ).head(limit)


def _scorecard_player_names(innings):
    """Return unique batting names from one innings in scorecard order."""
    names = []
    for batsman in innings.get("batsman", []):
        name = batsman.get("name")
        if name and name not in names:
            names.append(name)
    return names


def render_pre_match_player_analysis(innings_list, match_format=None):
    """Render current-scorecard player performance for pre-match discussion."""
    st.markdown("#### 👤 Player Performance — Pre-Match Discussion")

    team_blocks = []
    for innings in innings_list:
        team = innings.get("batteamname", "Team")
        names = _scorecard_player_names(innings)
        team_blocks.append((team, names))

    if len(team_blocks) < 2:
        st.caption("Player discussion data requires both team batting lineups.")
        return

    cols = st.columns(2, gap="large")

    for col, (team, player_names) in zip(cols, team_blocks[:2]):
        with col:
            st.markdown(f"**{team}**")
            analysis = get_pre_match_player_analysis(
                player_names,
                match_format,
                limit=5,
            )

            if analysis.empty:
                st.caption("No three-year batting history is available for these players.")
                continue

            display = analysis[
                [
                    "player_name",
                    "Innings",
                    "Runs",
                    "Avg",
                    "SR",
                    "Fifties",
                    "Momentum",
                ]
            ].copy()

            display.columns = [
                "Player",
                "Innings",
                "Runs",
                "Avg",
                "SR",
                "50+",
                "Momentum",
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn("Player", width="medium"),
                    "Innings": st.column_config.NumberColumn("Inn", width="small"),
                    "Runs": st.column_config.NumberColumn("Runs", width="small"),
                    "Avg": st.column_config.NumberColumn("Avg", width="small", format="%.1f"),
                    "SR": st.column_config.NumberColumn("SR", width="small", format="%.1f"),
                    "50+": st.column_config.NumberColumn("50+", width="small"),
                    "Momentum": st.column_config.NumberColumn("Momentum", width="small", format="%.1f"),
                },
            )

def render_scorecard_header(scorecard_data, innings_list, team1=None, team2=None):
    """Render the reference-style live scoreboard without raw HTML."""
    teams = []
    for innings in innings_list:
        team = innings.get("batteamname")
        if team and team not in teams:
            teams.append(team)
    for team in (team1, team2):
        if team and team not in teams:
            teams.append(team)
    teams = teams[:2]

    while len(teams) < 2:
        teams.append(f"Team {len(teams) + 1}")

    score_map = {}
    for innings in innings_list:
        team = innings.get("batteamname", "Team")
        score_map.setdefault(team, []).append(
            (
                innings.get("score", 0),
                innings.get("wickets", 0),
                innings.get("overs", 0),
            )
        )

    st.markdown("### LIVE SCORECARD")
    col1, col2 = st.columns(2, gap="small")

    for col, team in zip((col1, col2), teams):
        with col:
            with st.container(border=True):
                st.markdown(f"**{team}**")
                innings_scores = score_map.get(team, [])
                if innings_scores:
                    for score, wickets, overs in innings_scores:
                        st.markdown(f"## {score}/{wickets}")
                        st.caption(f"{overs} overs")
                else:
                    st.markdown("## —")
                    st.caption("Score unavailable")

def render_scorecard_player_analytics(innings_list, match_format=None):
    """Render player form and momentum for current scorecard players."""
    history = get_historical_player_innings()

    if history.empty:
        st.info("Historical player form data is unavailable.")
        return

    player_names = []

    for innings in innings_list:
        for batsman in innings.get("batsman", []):
            name = batsman.get("name")
            if name and name not in player_names:
                player_names.append(name)

    analytics = []

    for player_name in player_names:
        item = get_player_form_analytics(
            player_name,
            history,
            match_format,
        )
        if item:
            analytics.append(item)

    if not analytics:
        st.info(
            "No three-year batting history is available for the players in this innings."
        )
        return

    analytics.sort(
        key=lambda item: (
            item["momentum_score"],
            item["avg_last5"],
        ),
        reverse=True,
    )

    st.markdown("#### 📊 Player Form & Momentum")

    selected_player = st.selectbox(
        "Player",
        [item["player"] for item in analytics],
        key=f"scorecard_player_{hash(tuple(player_names))}",
    )

    selected = next(
        item
        for item in analytics
        if item["player"] == selected_player
    )

    metric_col1, metric_col2 = st.columns(2)

    with metric_col1:
        st.metric("Form", selected["form"])
        st.metric("Avg L5", f"{selected['avg_last5']:.1f}")
        st.metric("SR L5", f"{selected['sr_last5']:.1f}")

    with metric_col2:
        st.metric(
            "Momentum",
            f"{selected['momentum_score']:.0f}/100",
        )
        st.metric("Avg L10", f"{selected['avg_last10']:.1f}")
        st.metric("50+ Scores", selected["fifty_plus"])

    trend_df = selected["recent"][
        ["match_date", "runs_scored"]
    ].copy()

    trend_df = trend_df.sort_values("match_date")

    if not trend_df.empty:
        trend_df["Match"] = range(1, len(trend_df) + 1)

        st.line_chart(
            trend_df.set_index("Match")["runs_scored"],
            height=150,
        )

    delta = selected["momentum_delta"]

    if delta > 0:
        st.success(
            f"Momentum rising: recent 5-innings average is "
            f"{delta:.1f} runs above the previous 5."
        )
    elif delta < 0:
        st.warning(
            f"Momentum cooling: recent 5-innings average is "
            f"{abs(delta):.1f} runs below the previous 5."
        )
    else:
        st.info("Momentum is stable across the latest 10 innings.")


def render_historical_prediction_context(
    team1,
    team2,
    match_format=None,
    venue=None,
    city=None,
):
    """Render historical performance signals used for prediction/price analysis."""
    context = get_historical_prediction_context(
        team1,
        team2,
        match_format,
        venue,
        city,
    )

    st.markdown("#### 📈 Historical Performance & Price Indicator")

    prob_col1, prob_col2 = st.columns(2)

    with prob_col1:
        st.metric(
            f"{team1} historical probability",
            f"{context['prob1']:.1f}%",
        )
        st.caption(
            f"Historical fair-price indicator: "
            f"{context['fair_odds1']:.2f}"
            if context["fair_odds1"] is not None
            else "Fair-price indicator unavailable."
        )

    with prob_col2:
        st.metric(
            f"{team2} historical probability",
            f"{context['prob2']:.1f}%",
        )
        st.caption(
            f"Historical fair-price indicator: "
            f"{context['fair_odds2']:.2f}"
            if context["fair_odds2"] is not None
            else "Fair-price indicator unavailable."
        )

    form_df = pd.DataFrame(
        {
            "Team": [team1, team2],
            "Recent Win %": [
                context["form1"]["win_pct"],
                context["form2"]["win_pct"],
            ],
            "Last Matches": [
                context["form1"]["matches"],
                context["form2"]["matches"],
            ],
        }
    )

    st.bar_chart(
        form_df.set_index("Team")[["Recent Win %"]],
        height=150,
    )

    st.caption(
        "Historical indicator combines three-year H2H, recent team form, "
        "and venue performance when sufficient data exists. "
        "It is not bookmaker odds or a betting recommendation."
    )



def _extract_api_match_infos(payload):
    """Extract matchInfo dictionaries from a Cricbuzz API response."""
    found = []

    def walk(value):
        if isinstance(value, dict):
            match_info = value.get("matchInfo")
            if isinstance(match_info, dict):
                found.append(match_info)
            elif "matchId" in value and (
                isinstance(value.get("team1"), dict)
                or isinstance(value.get("team2"), dict)
            ):
                found.append(value)

            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return found


def _api_team_name(value):
    """Extract a team name from a Cricbuzz team object."""
    if isinstance(value, dict):
        return (
            value.get("teamName")
            or value.get("name")
            or value.get("shortName")
            or value.get("teamSName")
            or ""
        )
    return str(value or "")


def _api_team_id(value):
    """Extract a Cricbuzz team ID from a team object."""
    if isinstance(value, dict):
        return value.get("teamId") or value.get("id")
    return value


def _api_venue_id(venue_info):
    """Extract a venue ID when Cricbuzz includes one in match metadata."""
    if not isinstance(venue_info, dict):
        return None
    return (
        venue_info.get("venueId")
        or venue_info.get("id")
        or venue_info.get("groundId")
    )


def _api_series_id(info):
    """Extract a series ID from match metadata."""
    if not isinstance(info, dict):
        return None
    return info.get("seriesId") or info.get("seriesID")


def _api_match_date(match_info):
    """Convert a Cricbuzz match start timestamp into a pandas timestamp."""
    value = match_info.get("startDate") or match_info.get("startDt")
    if value in (None, ""):
        return pd.NaT
    try:
        return pd.to_datetime(int(value), unit="ms", errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return pd.to_datetime(value, errors="coerce")


def _api_winner_from_status(status, team1, team2):
    """Infer a winner from Cricbuzz's human-readable result/status text."""
    text = str(status or "").strip()
    lowered = text.lower()
    if "won by" not in lowered:
        return ""

    winner_text = text[:lowered.find("won by")].strip()
    winner_key = _team_match_name_key(winner_text)

    for team in (team1, team2):
        key = _team_match_name_key(team)
        if key and (winner_key == key or winner_key.startswith(key) or key.startswith(winner_key)):
            return team

    return winner_text


def _normalize_h2h_api_results(team1, team2, team1_payload, team2_payload):
    """Build a compact H2H table from Cricbuzz team-results responses."""
    records = {}
    target1 = _team_match_name_key(team1)
    target2 = _team_match_name_key(team2)

    for payload in (team1_payload, team2_payload):
        for info in _extract_api_match_infos(payload):
            left = _api_team_name(info.get("team1", {}))
            right = _api_team_name(info.get("team2", {}))
            left_key = _team_match_name_key(left)
            right_key = _team_match_name_key(right)

            if not (
                (left_key == target1 and right_key == target2)
                or (left_key == target2 and right_key == target1)
            ):
                continue

            match_id = info.get("matchId") or info.get("id")
            key = str(match_id) if match_id not in (None, "") else f"{_api_match_date(info)}|{left}|{right}"
            status = info.get("status") or info.get("result") or info.get("resultText") or ""

            records[key] = {
                "Date": _api_match_date(info),
                "Format": info.get("matchFormat") or info.get("matchType") or "",
                "Team 1": left,
                "Team 2": right,
                "Winner": _api_winner_from_status(status, team1, team2),
                "Venue": (info.get("venueInfo") or {}).get("ground", ""),
                "Result": status,
                "Match ID": match_id,
            }

    df = pd.DataFrame(records.values())
    if df.empty:
        return df

    cutoff = pd.Timestamp.now() - pd.DateOffset(years=3)
    df = df[(df["Date"].isna()) | (df["Date"] >= cutoff)].copy()
    return df.sort_values("Date", ascending=False, na_position="last").reset_index(drop=True)


def _venue_stats_tables(payload):
    """Extract table-shaped sections from the venue-stats API response."""
    tables = []

    def walk(value, label="Venue statistics"):
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            frame = pd.DataFrame(value)
            if not frame.empty:
                tables.append((label, frame))
            return

        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    walk(child, str(key))

    walk(payload)
    return tables


def _history_api_error_details(payload):
    """Return diagnostic details attached to a failed history API response."""
    if not isinstance(payload, dict):
        return {
            "status": None,
            "error_type": "unknown",
            "detail": "The API returned an unusable response.",
        }

    return {
        "status": payload.get("_api_http_status"),
        "error_type": payload.get("_api_error_type") or "unknown",
        "detail": payload.get("_api_error_detail") or "",
    }


def _render_history_api_error(title, payload, subject):
    """Show an actionable distinction between missing data and API failure."""
    details = _history_api_error_details(payload)
    status = details["status"]
    error_type = details["error_type"]
    detail = details["detail"]

    if error_type == "missing_key":
        reason = "API key is missing or not configured."
        action = "Check CRICBUZZ_API_KEY in your local .env or Streamlit secrets."
    elif error_type == "authentication":
        reason = "The API rejected the supplied credentials."
        action = "Check that CRICBUZZ_API_KEY is valid and active."
    elif error_type == "access":
        reason = "The API endpoint is not available to the current subscription/access plan."
        action = "Check your RapidAPI subscription and endpoint access."
    elif error_type == "rate_limit":
        reason = "The API rate limit or quota has been reached."
        action = "Wait and try again later, or check the remaining RapidAPI quota."
    elif error_type == "endpoint":
        reason = "The requested API endpoint or resource was not found."
        action = "Check the endpoint/resource configuration. This is not evidence that historical data is missing."
    elif error_type == "server":
        reason = "The Cricbuzz/RapidAPI server returned an error."
        action = "Try again later."
    elif error_type == "timeout":
        reason = "The API request timed out."
        action = "Check the connection and try again."
    elif error_type == "network":
        reason = "The API could not be reached because of a connection problem."
        action = "Check the internet connection and try again."
    elif error_type == "invalid_json":
        reason = "The API returned a successful status, but the response was not valid JSON."
        action = "Try again later."
    else:
        reason = "The API request failed before usable historical data could be returned."
        action = "Try again later and check the API status if the problem persists."

    status_text = f"HTTP {status}" if status is not None else "No HTTP status"

    st.warning(f"⚠️ {title} could not be loaded for {subject}.")
    with st.container(border=True):
        st.markdown(f"**What happened**  \n{reason}")
        st.markdown(f"**API status:** `{status_text}`")
        st.markdown("**How to distinguish this from missing historical data**  \nThe API did **not** return a successful historical-data response, so this result does **not** mean that the history is absent.")
        st.markdown(f"**What to do:** {action}")
        if detail:
            st.caption(f"API response: {detail}")


def _render_history_cached_warning(title, payload):
    """Explain when stale cached data is being shown after an API failure."""
    details = _history_api_error_details(payload)
    status = details["status"]
    error_type = details["error_type"]

    if status is not None:
        status_text = f"HTTP {status}"
    else:
        status_text = error_type.replace("_", " ").title()

    age = payload.get("_cache_age_seconds")
    if age is None:
        age_text = "cached data"
    elif age < 3600:
        age_text = f"cache is {max(1, age // 60)} minute(s) old"
    else:
        age_text = f"cache is {age // 3600} hour(s) old"

    st.info(
        f"📦 **Showing cached {title}** — the latest API request could not be completed "
        f"({status_text}), so the app is using the previously saved response. "
        f"The {age_text}."
    )


def render_api_h2h_history(team1, team2, team1_id, team2_id, match_format=None, match_id=None):
    """Load H2H history from Cricbuzz only when requested."""
    if not team1_id or not team2_id:
        st.warning(
            "Cricbuzz did not provide team IDs for this match, so H2H History cannot be loaded from the API."
        )
        return

    if not st.button(
        "🤝 H2H History",
        key=f"api_h2h_btn_{match_id}",
        use_container_width=True,
    ):
        st.info(
            "Click H2H History to load the latest available team-vs-team history from the Cricbuzz API. "
            "A successful response is cached so repeated clicks do not make unnecessary API calls."
        )
        return

    with st.spinner("Loading H2H history from Cricbuzz…"):
        team1_data = get_team_results(str(team1_id))
        team2_data = get_team_results(str(team2_id))

    failed = []
    for team_name, payload in ((team1, team1_data), (team2, team2_data)):
        if isinstance(payload, dict) and "error" in payload:
            failed.append((team_name, payload))

    if failed:
        for team_name, payload in failed:
            _render_history_api_error("H2H History", payload, f"{team_name} results")
        return

    fallback_payloads = [
        payload
        for payload in (team1_data, team2_data)
        if isinstance(payload, dict) and payload.get("_data_source") == "fallback"
    ]
    for payload in fallback_payloads:
        _render_history_cached_warning("H2H History", payload)

    h2h_df = _normalize_h2h_api_results(team1, team2, team1_data, team2_data)

    if h2h_df.empty:
        st.info(
            f"ℹ️ **No H2H history found for {team1} vs {team2}.**\n\n"
            "The Cricbuzz API responded successfully (**HTTP 200**), but no matching "
            "head-to-head matches were returned in the selected three-year window. "
            "**This is not an API quota, authentication, or connection error.**"
        )
        return

    if match_format:
        fmt = str(match_format).strip().lower()
        format_df = h2h_df[h2h_df["Format"].astype(str).str.lower().eq(fmt)]
        if not format_df.empty:
            h2h_df = format_df.copy()

    team1_wins = int(h2h_df["Winner"].map(lambda x: _same_team(x, team1)).sum())
    team2_wins = int(h2h_df["Winner"].map(lambda x: _same_team(x, team2)).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Meetings", len(h2h_df))
    c2.metric(team1, team1_wins)
    c3.metric(team2, team2_wins)

    display = h2h_df[
        ["Date", "Team 1", "Team 2", "Winner", "Format", "Venue", "Result"]
    ].copy()
    display["Date"] = pd.to_datetime(
        display["Date"],
        errors="coerce",
    ).dt.strftime("%d %b %Y")
    display["Date"] = display["Date"].fillna("Date unavailable")

    st.dataframe(
        display.head(10),
        use_container_width=True,
        hide_index=True,
    )

    source1 = team1_data.get("_data_source", "cache") if isinstance(team1_data, dict) else "cache"
    source2 = team2_data.get("_data_source", "cache") if isinstance(team2_data, dict) else "cache"
    st.caption(
        f"Cricbuzz API history • source: {source1} + {source2} • "
        "successful API responses are persisted in data/api_cache"
    )


def render_api_venue_history(venue, city, venue_id, series_id, match_id=None):
    """Load venue history from Cricbuzz only when requested."""
    if not st.button(
        "🏟️ Venue History",
        key=f"api_venue_btn_{match_id}",
        use_container_width=True,
    ):
        st.info(
            "Click Venue History to load venue history from the Cricbuzz API. "
            "A successful response is cached so repeated clicks do not make unnecessary API calls."
        )
        return

    resolved_venue_id = venue_id

    if not resolved_venue_id and series_id:
        with st.spinner("Finding venue details from Cricbuzz…"):
            series_data = get_series_venues(str(series_id))

        if isinstance(series_data, dict) and "error" in series_data:
            _render_history_api_error("Venue History", series_data, "venue resolution")
            return

        if isinstance(series_data, dict):
            candidates = []

            def walk(value):
                if isinstance(value, dict):
                    if any(k in value for k in ("ground", "groundName", "venueName")):
                        candidates.append(value)
                    for child in value.values():
                        if isinstance(child, (dict, list)):
                            walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)

            walk(series_data)
            target_ground = _team_match_name_key(venue)
            target_city = _team_match_name_key(city)

            for candidate in candidates:
                candidate_ground = _team_match_name_key(
                    candidate.get("ground")
                    or candidate.get("groundName")
                    or candidate.get("venueName")
                )
                candidate_city = _team_match_name_key(candidate.get("city"))

                if candidate_ground == target_ground and (
                    not target_city
                    or not candidate_city
                    or candidate_city == target_city
                ):
                    resolved_venue_id = (
                        candidate.get("venueId")
                        or candidate.get("id")
                        or candidate.get("groundId")
                    )
                    if resolved_venue_id:
                        break

    if not resolved_venue_id:
        st.warning(
            "⚠️ Venue History could not be loaded. Cricbuzz did not provide a venue ID "
            "for this match, so the API cannot identify the venue history source."
        )
        return

    with st.spinner("Loading venue history from Cricbuzz…"):
        venue_data = get_venue_matches(str(resolved_venue_id))

    if not isinstance(venue_data, dict) or "error" in venue_data:
        _render_history_api_error("Venue History", venue_data, venue or "this venue")
        return

    if venue_data.get("_data_source") == "fallback":
        _render_history_cached_warning("Venue History", venue_data)

    # The venue matches endpoint is the primary source for venue history.
    # It is persisted by fetch_or_cache, so repeated clicks reuse the cache
    # instead of making another API request while the cache is fresh.
    venue_matches = []

    def walk_matches(value):
        if isinstance(value, dict):
            match_list = value.get("match")
            if isinstance(match_list, list):
                venue_matches.extend(match_list)

            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk_matches(child)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, (dict, list)):
                    walk_matches(child)

    walk_matches(venue_data.get("matchDetails", venue_data))

    rows = []
    seen_ids = set()

    for item in venue_matches:
        if not isinstance(item, dict):
            continue

        info = item.get("matchInfo", {})
        if not isinstance(info, dict):
            continue

        match_id = info.get("matchId") or info.get("id")
        if match_id in seen_ids:
            continue
        if match_id not in (None, ""):
            seen_ids.add(match_id)

        teams_1 = info.get("team1", {}) or {}
        teams_2 = info.get("team2", {}) or {}

        rows.append(
            {
                "Date": pd.to_datetime(
                    pd.to_numeric(info.get("startDate"), errors="coerce"),
                    unit="ms",
                    errors="coerce",
                ),
                "Team 1": teams_1.get("teamName", ""),
                "Team 2": teams_2.get("teamName", ""),
                "Format": info.get("matchFormat", ""),
                "Series": info.get("seriesName", ""),
                "Result": info.get("status", ""),
                "Match ID": match_id,
            }
        )

    venue_df = pd.DataFrame(rows)

    if venue_df.empty:
        st.info(
            f"ℹ️ **No venue history found for {venue or 'this venue'}.**\n\n"
            "The Cricbuzz API responded successfully (**HTTP 200**), but no venue "
            "matches were returned. **This is not an API quota or connection error.**"
        )
        return

    # Keep the requested three-year history window.
    cutoff = pd.Timestamp.now() - pd.DateOffset(years=3)
    venue_df = venue_df[
        venue_df["Date"].isna() | (venue_df["Date"] >= cutoff)
    ].copy()
    venue_df = venue_df.sort_values(
        "Date",
        ascending=False,
        na_position="last",
    )

    if venue_df.empty:
        st.info(
            f"ℹ️ **No venue history found for {venue or 'this venue'} in the last 3 years.**\n\n"
            "The Cricbuzz API responded successfully, but the venue endpoint returned "
            "no matches inside the selected three-year window. **This is not an API quota error.**"
        )
        return

    completed = venue_df[
        venue_df["Result"].astype(str).str.strip().ne("")
        & ~venue_df["Result"].astype(str).str.contains(
            "upcoming|scheduled",
            case=False,
            na=False,
        )
    ]

    c1, c2, c3 = st.columns(3)
    c1.metric("Matches", len(venue_df))
    c2.metric("Completed", len(completed))
    c3.metric("Series", venue_df["Series"].nunique())

    display = venue_df.head(15).copy()
    display["Date"] = display["Date"].dt.strftime("%d %b %Y")
    display["Date"] = display["Date"].fillna("Date unavailable")

    st.dataframe(
        display[
            [
                "Date",
                "Team 1",
                "Team 2",
                "Format",
                "Series",
                "Result",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Cricbuzz venue history • {venue or 'Venue'}"
        f"{f' • {city}' if city else ''} • "
        f"source: {venue_data.get('_data_source', 'cache')} • "
        "successful API responses are persisted in data/api_cache"
    )


def render_h2h_analytics(team1, team2, match_format=None):
    """Render three-year head-to-head analytics."""
    h2h = get_h2h_analytics(
        team1,
        team2,
        match_format,
    )

    st.markdown("#### 🤝 Head-to-Head — Last 3 Years")

    if h2h["total"] == 0:
        st.info(
            "No completed head-to-head matches were found in the three-year database window."
        )
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Meetings", h2h["total"])

    with col2:
        st.metric(team1, h2h["team1_wins"])

    with col3:
        st.metric(team2, h2h["team2_wins"])

    with col4:
        st.metric(
            "Other",
            h2h["ties"] + h2h["no_results"],
        )

    chart_df = pd.DataFrame(
        {
            "Team": [team1, team2],
            "Wins": [
                h2h["team1_wins"],
                h2h["team2_wins"],
            ],
        }
    )

    st.bar_chart(
        chart_df.set_index("Team"),
        height=150,
    )

    recent = h2h["matches"].head(5).copy()

    if not recent.empty:
        display = recent[
            [
                "match_date",
                "team1",
                "team2",
                "winner",
                "match_type",
                "venue_name",
            ]
        ].copy()

        display["match_date"] = display["match_date"].dt.strftime(
            "%d %b %Y"
        )

        display.columns = [
            "Date",
            "Team 1",
            "Team 2",
            "Winner",
            "Format",
            "Venue",
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
        )


def render_venue_analytics(
    team1,
    team2,
    venue,
    city=None,
    match_format=None,
):
    """Render three-year venue-specific performance insights."""
    venue_df = get_venue_analytics(
        team1,
        team2,
        venue,
        city,
        match_format,
    )

    st.markdown("#### 🏟️ Venue Performance — Last 3 Years")

    if venue_df.empty:
        st.info(
            "No three-year historical matches were found at this venue."
        )
        return

    st.dataframe(
        venue_df,
        use_container_width=True,
        hide_index=True,
    )

    chart_df = venue_df.set_index("Team")[["Win %"]]

    st.bar_chart(
        chart_df,
        height=150,
    )


def render_historical_trends(
    team1,
    team2,
    match_format=None,
):
    """Render recent historical trends that support match prediction."""
    history = get_historical_match_data()

    st.markdown("#### 📊 Historical Trends — Match Prediction")

    if history.empty:
        st.info("Historical match data is unavailable.")
        return

    rows = []

    for team in (team1, team2):
        form = get_team_recent_form(
            team,
            history,
            match_format,
            limit=10,
        )

        rows.append(
            {
                "Team": team,
                "Last 10": form["matches"],
                "Wins": form["wins"],
                "Losses": form["losses"],
                "No Result": form["no_results"],
                "Win %": form["win_pct"],
            }
        )

    trend_df = pd.DataFrame(rows)

    st.dataframe(
        trend_df,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        trend_df.set_index("Team")[["Win %"]],
        height=150,
    )



def render_innings_compact(innings):
    """Render one innings in a compact, reference-style scorecard."""
    team_name = innings.get("batteamname", "Batting Team")
    score = innings.get("score", 0)
    wickets = innings.get("wickets", 0)
    overs = innings.get("overs", 0)
    run_rate = innings.get("runrate")

    st.markdown(f"#### {team_name} · {score}/{wickets}")
    st.caption(f"{overs} overs" + (f" · Current Run Rate: {run_rate}" if run_rate is not None else ""))

    batting_df = create_batting_dataframe(innings.get("batsman", []))

    if not batting_df.empty:
        st.markdown("##### 🏏 Batting")
        batting_display = batting_df[
            ["Batter", "R", "B", "4s", "6s", "SR"]
        ].copy()

        st.dataframe(
            batting_display,
            use_container_width=True,
            hide_index=True,
            height=min(360, 42 + len(batting_display) * 35),
            column_config={
                "Batter": st.column_config.TextColumn("Batter", width="medium"),
                "R": st.column_config.NumberColumn("R", width="small"),
                "B": st.column_config.NumberColumn("B", width="small"),
                "4s": st.column_config.NumberColumn("4s", width="small"),
                "6s": st.column_config.NumberColumn("6s", width="small"),
                "SR": st.column_config.NumberColumn("SR", width="small", format="%.1f"),
            },
        )

        dismissal_df = batting_df[
            ["Batter", "Dismissal"]
        ].copy()
        dismissal_df = dismissal_df[
            dismissal_df["Dismissal"].astype(str).str.strip().ne("not out")
        ]
        if not dismissal_df.empty:
            with st.expander("Dismissals", expanded=False):
                st.dataframe(
                    dismissal_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Batter": st.column_config.TextColumn("Batter", width="medium"),
                        "Dismissal": st.column_config.TextColumn("Dismissal", width="large"),
                    },
                )

    bowling_df = create_bowling_dataframe(innings.get("bowler", []))
    if not bowling_df.empty:
        st.markdown("##### 🎯 Bowling")
        st.dataframe(
            bowling_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Bowler": st.column_config.TextColumn("Bowler", width="medium"),
                "O": st.column_config.TextColumn("O", width="small"),
                "M": st.column_config.NumberColumn("M", width="small"),
                "R": st.column_config.NumberColumn("R", width="small"),
                "W": st.column_config.NumberColumn("W", width="small"),
                "Econ": st.column_config.NumberColumn("Econ", width="small", format="%.1f"),
            },
        )

    extras = innings.get("extras", {})
    if extras:
        st.markdown("##### Extras")
        extras_df = pd.DataFrame([
            {
                "Byes": extras.get("byes", 0),
                "Leg Byes": extras.get("legbyes", 0),
                "Wides": extras.get("wides", 0),
                "No Balls": extras.get("noballs", 0),
                "Penalty": extras.get("penalty", 0),
                "Total": extras.get("total", 0),
            }
        ])
        st.dataframe(extras_df, use_container_width=True, hide_index=True)

    fow_data = innings.get("fow", {}).get("fow", [])
    if fow_data:
        with st.expander("Fall of Wickets", expanded=False):
            st.dataframe(
                pd.DataFrame([
                    {
                        "Batter": wicket.get("batsmanname", ""),
                        "Score": wicket.get("runs", ""),
                        "Over": wicket.get("overnbr", ""),
                    }
                    for wicket in fow_data
                ]),
                use_container_width=True,
                hide_index=True,
            )

    powerplay_data = innings.get("pp", {}).get("powerplay", [])
    if powerplay_data:
        with st.expander("Powerplay", expanded=False):
            st.dataframe(
                pd.DataFrame([
                    {
                        "Type": powerplay.get("pptype", ""),
                        "Overs": f"{powerplay.get('ovrfrom', '')} - {powerplay.get('ovrto', '')}",
                        "Runs": powerplay.get("run", 0),
                        "Wickets": powerplay.get("wickets", 0),
                    }
                    for powerplay in powerplay_data
                ]),
                use_container_width=True,
                hide_index=True,
            )

def render_match_scorecard(
    scorecard_data,
    team1=None,
    team2=None,
    venue=None,
    city=None,
    match_format=None,
):
    """Render the scorecard only; match analytics live beside the match card."""
    innings_list = scorecard_data.get(
        "scorecard",
        [],
    )

    if not innings_list:
        st.warning(
            "No detailed scorecard data is available for this match."
        )
        return

    render_scorecard_header(
        scorecard_data,
        innings_list,
        team1=team1,
        team2=team2,
    )

    status = scorecard_data.get("status")

    if status:
        st.info(
            f"📌 {status}"
        )

    st.markdown("### Scorecard")

    for index, innings in enumerate(
        innings_list,
        start=1,
    ):
        innings_id = innings.get(
            "inningsid",
            index,
        )

        with st.container(border=True):
            st.markdown(
                f"#### Innings {innings_id} · "
                f"{html.escape(str(innings.get('batteamname', 'Team')))}"
            )
            render_innings_compact(innings)


def get_cached_live_scorecard(match_id, force_refresh=False):
    """Return a session-cached scorecard, bypassing cache only on explicit request."""
    if match_id in (None, ""):
        return None

    cache_key = str(match_id)
    cache = st.session_state.setdefault("analytics_scorecards", {})

    # Explicit player-performance load/refresh is the only path that
    # bypasses the API helper cache.
    if force_refresh:
        scorecard = get_match_scorecard(cache_key, force_refresh=True)

        if isinstance(scorecard, dict) and "error" not in scorecard:
            cache[cache_key] = scorecard

        return scorecard

    # Normal reruns use the in-session scorecard first.
    if cache_key in cache:
        return cache[cache_key]

    # First non-interactive access uses the persistent/API helper cache.
    scorecard = get_match_scorecard(cache_key)

    if isinstance(scorecard, dict) and "error" not in scorecard:
        cache[cache_key] = scorecard
        return scorecard

    return scorecard


def render_live_match_analytics(
    match_id,
    team1,
    team2,
    venue=None,
    city=None,
    match_format=None,
    team1_id=None,
    team2_id=None,
    venue_id=None,
    series_id=None,
):
    """Render match analytics in the open space beside each live match card."""
    st.markdown(
        "### 📊 Match Intelligence"
    )
    st.caption(
        "Historical trends, player performance, head-to-head, venue signals, "
        "prediction context, and recent player form."
    )

    trend_tab, players_tab, h2h_tab, intelligence_tab, form_tab = st.tabs(
        [
            "📈 Trends",
            "👤 Players",
            "🤝 H2H & Venue",
            "🎯 Intelligence",
            "⚡ Player Form",
        ]
    )

    with trend_tab:
        render_historical_trends(
            team1 or "",
            team2 or "",
            match_format,
        )

    with players_tab:
        st.markdown("#### 👤 Player Performance — Pre-Match Discussion")
        st.caption(
            "Uses the current match scorecard and three-year batting history."
        )

        scorecard = None
        scorecard_key = f"analytics_players_loaded_{match_id}"

        load_player_performance = st.button(
            "👤 Load player performance",
            key=f"analytics_players_btn_{match_id}",
            use_container_width=True,
        )

        if load_player_performance:
            st.session_state[scorecard_key] = True

        if not st.session_state.get(scorecard_key):
            st.info(
                "Player analytics are loaded on request so the live page does not "
                "make an additional scorecard API call for every match."
            )
        else:
            # Only the explicit Load button bypasses the scorecard cache.
            # Subsequent reruns use the cached scorecard.
            scorecard = get_cached_live_scorecard(
                match_id,
                force_refresh=load_player_performance,
            )

            if not isinstance(scorecard, dict) or "error" in scorecard:
                error_text = (
                    scorecard.get("error", "Scorecard is unavailable.")
                    if isinstance(scorecard, dict)
                    else "Scorecard is unavailable."
                )
                st.warning(error_text)
            else:
                innings_list = scorecard.get("scorecard", [])
                render_pre_match_player_analysis(
                    innings_list,
                    match_format,
                )

    with h2h_tab:
        h2h_col, venue_col = st.columns(
            2,
            gap="large",
        )

        with h2h_col:
            st.markdown("#### 🤝 H2H History")
            render_api_h2h_history(
                team1 or "",
                team2 or "",
                team1_id,
                team2_id,
                match_format,
                match_id,
            )

        with venue_col:
            st.markdown("#### 🏟️ Venue History")
            render_api_venue_history(
                venue or "",
                city,
                venue_id,
                series_id,
                match_id,
            )

    with intelligence_tab:
        render_historical_prediction_context(
            team1 or "",
            team2 or "",
            match_format,
            venue or "",
            city,
        )

        st.caption(
            "Historical indicator combines three-year H2H, recent team form, "
            "and venue performance when sufficient data exists. It is not bookmaker "
            "odds or a betting recommendation."
        )

    with form_tab:
        st.markdown("#### 📊 Player Form & Momentum")
        st.caption(
            "Select a current player to inspect recent batting form and momentum."
        )

        scorecard_key = f"analytics_form_loaded_{match_id}"

        if st.button(
            "⚡ Load player form",
            key=f"analytics_form_btn_{match_id}",
            use_container_width=True,
        ):
            st.session_state[scorecard_key] = True

        if not st.session_state.get(scorecard_key):
            st.info(
                "Player form is loaded on request to keep the live dashboard "
                "lightweight."
            )
        else:
            scorecard = get_cached_live_scorecard(match_id)

            if not isinstance(scorecard, dict) or "error" in scorecard:
                error_text = (
                    scorecard.get("error", "Scorecard is unavailable.")
                    if isinstance(scorecard, dict)
                    else "Scorecard is unavailable."
                )
                st.warning(error_text)
            else:
                render_scorecard_player_analytics(
                    scorecard.get("scorecard", []),
                    match_format,
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

# Match tabs
# Create tabs before loading live data so the refresh button controls
# whether this run uses the normal cache or forces a fresh API request.
tab_live, tab_recent = st.tabs(
    [
        "Live now",
        "Recent Matches",
    ]
)


# Live matches

with tab_live:

    refresh_live_scores = st.button(
        "🔄 Refresh live scores",
        key="refresh_live_scores",
        use_container_width=False,
    )

    # The refresh button is the only action that bypasses the persistent
    # live-score cache. There is no separate live_data call before this
    # button, so a click always reaches get_live_matches(force_refresh=True).
    data = get_live_matches(
        force_refresh=refresh_live_scores,
    )

    # Keep the sidebar synchronized with the exact response displayed below.
    render_sidebar_live_scores(data)

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
                for match_block in live_matches:

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

                    team1_id = _api_team_id(team1_data)
                    team2_id = _api_team_id(team2_data)

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

                    venue_id = _api_venue_id(venue_info)
                    series_id = _api_series_id(info)

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

                    match_col, analytics_col = st.columns(
                        [1.0, 1.35],
                        gap="medium",
                    )

                    with match_col:
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

                            # Live commentary
                            render_commentary_section(
                                match_id,
                                team1,
                                team2,
                            )

                            # Prediction and scorecard
                            if match_id is not None:
                                pred_key = str(match_id)

                                existing = (
                                    st.session_state["predictions"].get(
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
                                        [team1, team2],
                                        key=f"pred_select_{pred_key}",
                                        label_visibility="collapsed",
                                    )

                                    if st.button(
                                        "🔒 Lock Prediction",
                                        key=f"pred_btn_{pred_key}",
                                        use_container_width=True,
                                    ):
                                        st.session_state["predictions"][
                                            pred_key
                                        ] = {
                                            "team": pick,
                                            "resolved": False,
                                        }

                                        leveled_up = add_xp(5)

                                        st.toast(
                                            f"🔮 Prediction locked: {pick} +5 XP",
                                            icon="🎲",
                                        )

                                        if leveled_up:
                                            st.balloons()

                                        st.rerun()

                                if st.button(
                                    "🧾 View Scorecard",
                                    key=f"scard_{match_id}",
                                    use_container_width=True,
                                ):
                                    scorecard = get_match_scorecard(
                                        str(match_id)
                                    )

                                    if "error" in scorecard:
                                        st.warning(
                                            "Couldn't load the scorecard: "
                                            f"{scorecard['error']}"
                                        )
                                    else:
                                        award_scorecard_xp(match_id)
                                        render_match_scorecard(
                                            scorecard,
                                            team1=team1,
                                            team2=team2,
                                            venue=venue,
                                            city=city,
                                            match_format=match_format,
                                        )

                    with analytics_col:
                        with st.container(
                            border=True
                        ):
                            render_live_match_analytics(
                                match_id,
                                team1,
                                team2,
                                venue=venue,
                                city=city,
                                match_format=match_format,
                                team1_id=team1_id,
                                team2_id=team2_id,
                                venue_id=venue_id,
                                series_id=series_id,
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
                                        scorecard,
                                        team1=team1,
                                        team2=team2,
                                        venue=venue,
                                        city=city,
                                        match_format=match["Format"],
                                    )




st.caption(
    "Live data refreshes every 8 hours unless manually refreshed. "
    "Recent-match data refreshes every 24 hours. "
    "Player rankings refresh every 30 days. "
    "A persistent fallback cache is retained for up to 30 days. "
    "Predictions and scorecard activity are tracked per browser session."
)