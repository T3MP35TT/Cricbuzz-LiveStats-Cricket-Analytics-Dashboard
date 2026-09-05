import sys
import json
import time
from pathlib import Path

import pandas as pd
import textwrap
import streamlit as st

# Resolve imports from the project root so the page works consistently
# on Windows, GitHub, and Streamlit Community Cloud.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.db_connection import run_query
from utils.gamification import (
    init_game_state,
    add_xp,
    complete_mission,
)
from utils.theme import apply_theme


# Page configuration

st.set_page_config(
    page_title="Top Player Stats | Cricbuzz LiveStats",
    page_icon="📊",
    layout="wide",
)


# Sidebar navigation styling

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(
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
        box-shadow: 0 5px 16px rgba(0,0,0,0.18) !important;
    }

    [data-testid="stSidebarNav"] a:hover::before {
        background: rgba(180,185,255,0.70) !important;
        box-shadow: 0 0 7px rgba(160,165,255,0.45) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;
        background: linear-gradient(
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
        box-shadow: 0 0 9px rgba(170,175,255,0.85) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]:hover {
        transform: translateX(1px) !important;
        border-color: rgba(160,165,255,0.48) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# Page-specific sidebar information

with st.sidebar.container(border=True):

    st.markdown(
        "📊 **PLAYER RANKINGS**"
    )

    st.caption(
        "Batting & bowling performance by format"
    )

    st.markdown(
        "⭐ **Rating**"
    )
    st.caption(
        "Primary ranking metric for player position"
    )

    st.markdown(
        "🏏 **Points**"
    )
    st.caption(
        "Performance points shown alongside rating"
    )

    st.markdown(
        "📈 **Rating Power**"
    )
    st.caption(
        "Visual comparison of each player's rating"
    )

    st.markdown(
        "🏆 **Top Performers**"
    )
    st.caption(
        "Compare the highest-rated batsmen and bowlers"
    )

    st.caption(
        "Use the format selector to switch between "
        "ODI, Test and T20 rankings."
    )

st.sidebar.caption(
    "CRICBUZZ LIVESTATS"
)


init_game_state()

apply_theme(
    badge_text="📊 TOP PLAYER STATS • CRICKET ANALYTICS ARENA",
    title="Top Player Stats",
    subtitle="Batting & bowling leaderboards, live and historical",
    tagline="🏏 LEADERBOARDS &nbsp; • &nbsp; ⭐ STAR FAVORITES &nbsp; • &nbsp; 🕵️ TALENT SCOUT",
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

    .leaderboard-scroll {
        overflow-x: auto;
        width: 100%;
    }

    .leaderboard-row {
        min-width: 720px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.session_state.setdefault("favorite_players", set())
st.session_state.setdefault("top_stats_formats_seen", set())
st.session_state.setdefault("top_stats_formats_bonus_awarded", False)


def render_favorite_picker(category_key, fmt, names):
    """Lets the user star a favorite player from the currently shown list."""
    names = [n for n in names if n]

    if not names:
        return

    st.markdown("###### ⭐ Star your favorite")

    pick_key = f"fav_pick_{category_key}_{fmt}"
    picked = st.selectbox(
        "Pick a player to star",
        names,
        key=pick_key,
        label_visibility="collapsed",
    )

    if st.button(
        f"⭐ Star {picked}",
        key=f"fav_btn_{category_key}_{fmt}",
    ):
        favorites = st.session_state["favorite_players"]

        if picked in favorites:
            st.info(f"{picked} is already one of your starred players.")
        else:
            favorites.add(picked)
            complete_mission("players", celebrate=False)
            leveled_up = add_xp(5)
            st.toast(f"⭐ {picked} starred! +5 XP", icon="🌟")

            if leveled_up:
                st.balloons()

            milestone = len(favorites)

            if milestone % 5 == 0:
                bonus_leveled_up = add_xp(20, coins=10)
                st.toast(
                    f"🕵️ Talent Scout milestone: {milestone} players starred! "
                    "+20 XP, +10 coins",
                    icon="🏅",
                )

                if bonus_leveled_up:
                    st.balloons()

    if st.session_state["favorite_players"]:
        st.caption(
            "Starred so far: "
            + ", ".join(sorted(st.session_state["favorite_players"]))
        )


def get_rank_display(rank):
    """Return a visual rank icon and badge."""
    try:
        rank = int(rank)
    except (TypeError, ValueError):
        return "⚡", "SCOUT"

    if rank == 1:
        return "👑", "LEGEND"
    if rank == 2:
        return "🥈", "ELITE"
    if rank == 3:
        return "🥉", "ELITE"
    if rank <= 5:
        return "🔥", "TOP 5"

    return "⚡", "TOP 10"


def render_gamified_leaderboard(df, category, fmt, value_label="Points"):
    """Render a gamified leaderboard using native Streamlit components only.

    No HTML is used here. This avoids raw HTML being displayed by Streamlit
    while keeping the existing dark Cricbuzz theme.
    """
    if df.empty:
        return

    df = df.copy()

    for column in ["Rank", "Rating", "Points"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Rank"] = df["Rank"].fillna(0).astype(int)
    df["Rating"] = df["Rating"].fillna(0)
    df["Points"] = df["Points"].fillna(0)

    max_rating = max(float(df["Rating"].max()), 1.0)

    category_icon = "🏏" if category == "batsmen" else "🎯"
    category_label = (
        "BATTING POWER"
        if category == "batsmen"
        else "BOWLING POWER"
    )

    # Gamified section header

    st.markdown(
        f"### {category_icon} {fmt.upper()} Leaderboard"
    )

    st.caption(
        f"🏆 {category_label}  •  "
        f"{len(df)} players  •  Ranked by rating"
    )

    # Header row

    header_cols = st.columns(
        [0.55, 2.05, 1.25, 0.85, 0.90, 1.65, 0.90]
    )

    headers = [
        "RANK",
        "PLAYER",
        "COUNTRY",
        "RATING",
        "POINTS",
        "POWER",
        "STATUS",
    ]

    for column, header in zip(header_cols, headers):
        column.caption(header)

    # Player rows

    for _, player in df.iterrows():

        rank = int(player["Rank"])

        player_name = str(
            player.get("Player", "Unknown")
        )

        country = str(
            player.get("Country", "Unknown")
        )

        trend = str(
            player.get("Trend", "Flat")
        )

        rating = float(
            player.get("Rating", 0) or 0
        )

        points = float(
            player.get("Points", 0) or 0
        )

        power = min(
            max(rating / max_rating, 0.0),
            1.0,
        )

        if rank == 1:
            rank_display = "👑 #1"
            badge = "LEGEND"
        elif rank == 2:
            rank_display = "🥈 #2"
            badge = "ELITE"
        elif rank == 3:
            rank_display = "🥉 #3"
            badge = "ELITE"
        elif rank <= 5:
            rank_display = f"🔥 #{rank}"
            badge = "TOP 5"
        else:
            rank_display = f"⚡ #{rank}"
            badge = "TOP 10"

        trend_lower = trend.lower()

        if trend_lower in {
            "up",
            "rising",
            "increase",
            "↑",
        }:
            trend_display = "📈 Rising"
        elif trend_lower in {
            "down",
            "falling",
            "decrease",
            "↓",
        }:
            trend_display = "📉 Falling"
        else:
            trend_display = f"➖ {trend}"

        # Keep each player visually separated while using native Streamlit.

        with st.container(border=True):

            row_cols = st.columns(
                [0.55, 2.05, 1.25, 0.85, 0.90, 1.65, 0.90]
            )

            with row_cols[0]:
                st.markdown(
                    f"**{rank_display}**"
                )
                st.caption(badge)

            with row_cols[1]:
                st.markdown(
                    f"**{player_name}**"
                )

            with row_cols[2]:
                st.write(
                    f"🌍 {country}"
                )

            with row_cols[3]:
                st.markdown(
                    f"**{rating:,.0f}**"
                )

            with row_cols[4]:
                st.markdown(
                    f"**{points:,.0f}**"
                )
                st.caption(value_label)

            with row_cols[5]:
                st.caption(
                    f"Rating Power • {power * 100:.0f}%"
                )
                st.progress(
                    power,
                    text=None,
                )

            with row_cols[6]:
                st.markdown(
                    f"**{trend_display}**"
                )




# Page intro

st.write(
    "View the latest imported ICC batting and bowling rankings "
    "for ODI, Test and T20 formats."
)

st.caption(
    "🏆 Top 20 ICC-ranked players are shown separately for batting and bowling."
)


# Format selector

fmt = st.selectbox(
    "Format",
    ["odi", "test", "t20"],
    format_func=lambda x: x.upper(),
)

db_format = fmt.upper()


# Format Explorer bonus

st.session_state["top_stats_formats_seen"].add(fmt)

if (
    len(st.session_state["top_stats_formats_seen"]) >= 3
    and not st.session_state["top_stats_formats_bonus_awarded"]
):
    st.session_state["top_stats_formats_bonus_awarded"] = True

    leveled_up = add_xp(15, coins=5)

    st.toast(
        "🌍 Format Explorer: checked ODI, Test & T20! +15 XP, +5 coins",
        icon="🗺️",
    )

    if leveled_up:
        st.balloons()


def get_icc_rankings(format_code, ranking_type):
    """Load the top 20 ICC rankings directly from the format-specific table."""

    table_map = {
        "odi": "icc_rankings_odi",
        "test": "icc_rankings_test",
        "t20": "icc_rankings_t20",
    }

    table = table_map[format_code]

    query = f"""
        SELECT
            RANK() OVER (ORDER BY rating DESC) AS Rank,
            player AS Player,
            team AS Country,
            rating AS Rating,
            career_best_rating AS Career_Best_Rating
        FROM {table}
        WHERE ranking_type = ?
          AND rating IS NOT NULL
          AND rating > 0
        ORDER BY rating DESC, player ASC
        LIMIT 20
    """

    df = run_query(query, (ranking_type,))

    if df is None:
        return pd.DataFrame()

    return df


def render_icc_leaderboard(df, category, fmt):
    """Render a compact gamified ICC top-20 leaderboard."""

    if df.empty:
        st.warning(
            f"No ICC {category} rankings found for {fmt.upper()}."
        )
        return

    df = df.copy()

    for column in ["Rank", "Rating", "Career_Best_Rating"]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df["Rank"] = df["Rank"].fillna(0).astype(int)
    df["Rating"] = df["Rating"].fillna(0)
    df["Career_Best_Rating"] = df["Career_Best_Rating"].fillna(0)

    max_rating = max(float(df["Rating"].max()), 1.0)

    category_icon = "🏏" if category == "batsmen" else "🎯"
    category_label = (
        "ICC BATTING RANKINGS"
        if category == "batsmen"
        else "ICC BOWLING RANKINGS"
    )

    st.markdown(
        f"### {category_icon} ICC Top 20 {category.title()}"
    )

    st.caption(
        f"🏆 {category_label}  •  {len(df)} players  •  "
        f"{fmt.upper()} • Ranked by ICC rating"
    )

    header_cols = st.columns(
        [0.55, 2.05, 1.35, 0.90, 1.10, 1.65, 0.90]
    )

    headers = [
        "RANK",
        "PLAYER",
        "TEAM",
        "RATING",
        "CAREER BEST",
        "RATING POWER",
        "STATUS",
    ]

    for column, header in zip(header_cols, headers):
        column.caption(header)

    for _, player in df.iterrows():

        rank = int(player["Rank"])

        player_name = str(
            player.get("Player", "Unknown")
        )

        country = str(
            player.get("Country", "Unknown")
        )

        rating = float(
            player.get("Rating", 0) or 0
        )

        career_best = float(
            player.get("Career_Best_Rating", 0) or 0
        )

        power = min(
            max(rating / max_rating, 0.0),
            1.0,
        )

        if rank == 1:
            rank_display = "👑 #1"
            badge = "LEGEND"
        elif rank == 2:
            rank_display = "🥈 #2"
            badge = "ELITE"
        elif rank == 3:
            rank_display = "🥉 #3"
            badge = "ELITE"
        elif rank <= 5:
            rank_display = f"🔥 #{rank}"
            badge = "TOP 5"
        elif rank <= 10:
            rank_display = f"⚡ #{rank}"
            badge = "TOP 10"
        else:
            rank_display = f"🏅 #{rank}"
            badge = "TOP 20"

        with st.container(border=True):

            row_cols = st.columns(
                [0.55, 2.05, 1.35, 0.90, 1.10, 1.65, 0.90]
            )

            with row_cols[0]:
                st.markdown(f"**{rank_display}**")
                st.caption(badge)

            with row_cols[1]:
                st.markdown(f"**{player_name}**")

            with row_cols[2]:
                st.write(f"🌍 {country}")

            with row_cols[3]:
                st.markdown(f"**{rating:,.0f}**")

            with row_cols[4]:
                st.markdown(f"**{career_best:,.0f}**")

            with row_cols[5]:
                st.caption(
                    f"Rating Power • {power * 100:.0f}%"
                )
                st.progress(
                    power,
                    text=None,
                )

            with row_cols[6]:
                st.markdown("**ICC**")
                st.caption("Ranked")


# Two-column layout

col1, col2 = st.columns(2)


# Top 20 ICC batsmen

with col1:

    batsmen_df = get_icc_rankings(
        fmt,
        "batting",
    )

    render_icc_leaderboard(
        batsmen_df,
        "batsmen",
        fmt,
    )

    if not batsmen_df.empty:
        render_favorite_picker(
            "batsmen",
            fmt,
            batsmen_df["Player"].tolist(),
        )


# Top 20 ICC bowlers

with col2:

    bowlers_df = get_icc_rankings(
        fmt,
        "bowling",
    )

    render_icc_leaderboard(
        bowlers_df,
        "bowlers",
        fmt,
    )

    if not bowlers_df.empty:
        render_favorite_picker(
            "bowlers",
            fmt,
            bowlers_df["Player"].tolist(),
        )

