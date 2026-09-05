import streamlit as st
import pandas as pd
import json
import html
import base64
import mimetypes
from pathlib import Path

import plotly.express as px

from utils.db_connection import run_query
from utils.api_helper import _cache_key
from sql_queries.queries import QUERIES, Q22_VENUE_PERFORMANCE
from utils.theme import apply_theme


# Project-relative paths
#
# This file lives inside the pages/ directory, so:
#   Path(__file__).resolve().parent       -> pages/
#   Path(__file__).resolve().parent.parent -> project root/
#
# Using project-relative paths keeps the app portable across:
#   - Windows local development
#   - GitHub
#   - Streamlit Community Cloud / Linux
#   - Other deployment environments

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PLAYER_IMAGE_DIR = PROJECT_ROOT / "data" / "Images" / "IND Players"
INDIAN_FLAG_PATH = PROJECT_ROOT / "data" / "Images" / "Indian Flag.png"


def get_indian_flag_html():
    """Return the Indian flag image for the Q1 India Squad hero card."""
    if not INDIAN_FLAG_PATH.exists():
        return "🇮🇳"

    try:
        image_data = base64.b64encode(INDIAN_FLAG_PATH.read_bytes()).decode("utf-8")
        return f"""
        <img
            src="data:image/png;base64,{image_data}"
            alt="Indian Flag"
            style="
                width:42px;
                height:28px;
                object-fit:cover;
                border-radius:4px;
                display:block;
                box-shadow:0 2px 8px rgba(0,0,0,0.30);
            "
        >
        """
    except OSError:
        return "🇮🇳"


def get_player_image_html(player_name):
    """Return an embedded player image for the Q1 squad card."""
    if not player_name:
        return ""

    player_name = str(player_name).strip()
    supported_extensions = [".jpg", ".png"]

    image_path = None
    for extension in supported_extensions:
        candidate = PLAYER_IMAGE_DIR / f"{player_name}{extension}"
        if candidate.exists():
            image_path = candidate
            break

    # Handle filenames with different capitalization if needed.
    if image_path is None and PLAYER_IMAGE_DIR.exists():
        target_name = player_name.casefold()
        for candidate in PLAYER_IMAGE_DIR.iterdir():
            if (
                candidate.is_file()
                and candidate.suffix.lower() in supported_extensions
                and candidate.stem.casefold() == target_name
            ):
                image_path = candidate
                break

    if image_path is None:
        return """
        <div style="
            width:82px;
            height:82px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:36px;
            background:rgba(255,255,255,0.07);
            border:1px solid rgba(255,255,255,0.16);
            margin-bottom:10px;
        ">👤</div>
        """

    try:
        image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        return f"""
        <img
            src="data:{mime_type};base64,{image_data}"
            alt="{html.escape(player_name)}"
            style="
                width:82px;
                height:82px;
                object-fit:cover;
                object-position:center top;
                border-radius:50%;
                border:2px solid rgba(255,255,255,0.28);
                box-shadow:0 5px 18px rgba(0,0,0,0.30);
                display:block;
                margin-bottom:10px;
            "
        >
        """
    except OSError:
        return """
        <div style="
            width:82px;
            height:82px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:36px;
            background:rgba(255,255,255,0.07);
            border:1px solid rgba(255,255,255,0.16);
            margin-bottom:10px;
        ">👤</div>
        """



st.set_page_config(
    page_title="SQL Analytics | Cricbuzz LiveStats",
    page_icon="🔎",
    layout="wide"
)


# Sidebar navigation styling

st.markdown(
    """
    <style>

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                rgba(5, 8, 16, 0.99),
                rgba(8, 11, 20, 0.99)
            ) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebarNav"] {
        padding: 18px 12px 14px 12px !important;
    }

    [data-testid="stSidebarNav"] ul {
        padding: 0 !important;
        margin: 0 !important;
        gap: 4px !important;
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
    }

    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;

        background: rgba(255,255,255,0.055) !important;
        border-color: rgba(255,255,255,0.07) !important;

        transform: translateX(1px) !important;

        box-shadow:
            0 5px 16px rgba(0,0,0,0.16) !important;
    }

    [data-testid="stSidebarNav"] a:hover::before {
        background: rgba(190,195,255,0.72) !important;
        box-shadow:
            0 0 7px rgba(160,165,255,0.45) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;

        background:
            linear-gradient(
                90deg,
                rgba(120,126,255,0.25),
                rgba(115,120,220,0.12)
            ) !important;

        border: 1px solid rgba(145,150,255,0.42) !important;

        box-shadow:
            inset 3px 0 0 rgba(185,190,255,0.98),
            0 7px 20px rgba(0,0,0,0.24) !important;

        font-weight: 800 !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]::before {
        background: #cdd0ff !important;

        box-shadow:
            0 0 9px rgba(170,175,255,0.88) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]:hover {
        transform: translateX(1px) !important;
    }

    .sql-sidebar-card {
        margin-top: 18px;
        padding: 14px;
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 11px;
        background: rgba(255,255,255,0.025);
    }

    .sql-sidebar-card-title {
        color: rgba(255,255,255,0.88);
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    .sql-insight-icon {
        font-size: 18px;
        line-height: 1;
        padding-top: 2px;
    }

    .sql-insight-label {
        color: rgba(255,255,255,0.52);
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.55px;
        line-height: 1.2;
        text-transform: uppercase;
    }

    .sql-insight-value {
        color: #ffffff;
        font-size: 13px;
        font-weight: 800;
        line-height: 1.25;
        margin-top: 3px;
        overflow-wrap: anywhere;
    }

    .sql-sidebar-card-text {
        color: rgba(255,255,255,0.55);
        font-size: 10px;
        line-height: 1.45;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

apply_theme(
    title="🔎 SQL Queries & Analytics",
    subtitle="25 cricket analytics challenges powered by the local SQL database.",
    tagline="🔍 EXPLORE DATA • 🧠 SOLVE QUERIES • 🏆 MASTER ANALYTICS",
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
    </style>
    """,
    unsafe_allow_html=True,
)


# SQL Analytics sidebar insights
#
# The sidebar is intentionally data-driven.
# It shows facts calculated from the LAST QUERY THAT WAS ACTUALLY RUN.
# Selecting a query does not change these insights until Run query is clicked.


def _sidebar_find_column(df, candidates):
    """Find a dataframe column using case-insensitive candidate names."""
    if df is None or df.empty:
        return None

    normalized = {
        str(column).strip().lower().replace(" ", "_"): column
        for column in df.columns
    }

    for candidate in candidates:
        key = str(candidate).strip().lower().replace(" ", "_")
        if key in normalized:
            return normalized[key]

    return None


def _sidebar_numeric(df, column):
    """Return a numeric Series or None."""
    if not column or column not in df.columns:
        return None

    values = pd.to_numeric(df[column], errors="coerce").dropna()
    return values if not values.empty else None


def _sidebar_number(value):
    """Format numeric values compactly for the sidebar."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number.is_integer():
        return f"{int(number):,}"

    if abs(number) >= 1000:
        return f"{number:,.0f}"

    return f"{number:,.2f}".rstrip("0").rstrip(".")


def _sidebar_clean(value):
    """Clean a dataframe value for compact display."""
    if pd.isna(value):
        return "N/A"

    text_value = str(value).strip()

    if not text_value or text_value.lower() in {"none", "nan", "null"}:
        return "N/A"

    return text_value


def _sidebar_top_category(df, column):
    """Return the most common non-empty category and its count."""
    if not column or column not in df.columns:
        return None

    values = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[
        (values != "")
        & (~values.str.lower().isin(["none", "nan", "null", "unknown"]))
    ]

    if values.empty:
        return None

    counts = values.value_counts()

    return _sidebar_clean(counts.index[0]), int(counts.iloc[0])


def _sidebar_top_numeric(
    df,
    numeric_candidates,
    label_candidates,
    label,
    mode="max",
    suffix="",
):
    """
    Find the most important numeric result and attach its player/team/entity.

    Example:
        ("Run Leader", "Babar Azam", "5,432 runs")
    """
    numeric_column = _sidebar_find_column(df, numeric_candidates)

    if not numeric_column:
        return None

    numeric_values = pd.to_numeric(
        df[numeric_column],
        errors="coerce",
    )

    valid = df.loc[numeric_values.notna()].copy()

    if valid.empty:
        return None

    valid["_sidebar_metric"] = numeric_values.loc[valid.index]

    row = (
        valid.sort_values(
            "_sidebar_metric",
            ascending=(mode == "min"),
        )
        .iloc[0]
    )

    label_column = _sidebar_find_column(
        valid,
        label_candidates,
    )

    entity = (
        _sidebar_clean(row[label_column])
        if label_column
        else None
    )

    metric_value = _sidebar_number(row["_sidebar_metric"])

    if suffix:
        metric_text = f"{metric_value} {suffix}"
    else:
        metric_text = metric_value

    if entity and entity != "N/A":
        return label, entity, metric_text

    return label, metric_text, ""


def _sidebar_build_insights(query_choice, result_df):
    """
    Build four compact, factual sidebar insights from the actual query result.

    The function intentionally uses the columns returned by SQL rather than
    hard-coded values. If a query changes its output columns, unavailable
    insights simply fall back to other useful facts.
    """
    if result_df is None:
        return "📊 Query Insights", []

    df = result_df.copy()

    if df.empty:
        return "📊 Query Insights", [
            ("📭", "RESULT", "No rows returned", "The query returned an empty result.")
        ]

    query_text = str(query_choice or "")
    query_number = query_text.split(":", 1)[0].strip().upper()

    title_map = {
        "Q1": "🇮🇳 Squad Insights",
        "Q2": "🏟️ Match Insights",
        "Q3": "🏆 ODI Run Insights",
        "Q4": "🏟️ Venue Insights",
        "Q5": "🏆 Winning Insights",
        "Q6": "👤 Role Insights",
        "Q7": "🔥 Batting Insights",
        "Q8": "🏆 Series Insights",
        "Q9": "⚔️ All-Rounder Insights",
        "Q10": "⚔️ Recent Match Insights",
        "Q11": "📊 Q11 Insights",
        "Q12": "🏠 Home vs Away",
        "Q13": "🤝 Partnership Insights",
        "Q14": "🎯 Bowling Insights",
        "Q15": "🔥 Close Match Insights",
        "Q16": "📈 Trend Insights",
        "Q17": "🪙 Toss Insights",
        "Q18": "📊 Q18 Insights",
        "Q19": "🎯 Consistency Insights",
        "Q20": "🌍 Three-Format Insights",
        "Q21": "🏆 Performance Insights",
        "Q22": "⚔️ H2H Insights",
        "Q23": "🔥 Momentum Insights",
        "Q24": "🤝 Partnership Insights",
        "Q25": "🚀 Career Insights",
    }

    title = title_map.get(
        query_number,
        f"📊 {query_number or 'Query'} Insights",
    )

    insights = []

    def add(icon, label, value, detail=""):
        if value is None:
            return

        value = _sidebar_clean(value)

        if value == "N/A":
            return

        insights.append(
            (icon, label.upper(), value, detail)
        )

    # Always make the first insight the actual number of returned records.
    add(
        "📊",
        "Rows analyzed",
        f"{len(df):,}",
        "Records returned by the executed SQL query.",
    )

    if query_number == "Q1":
        role_col = _sidebar_find_column(
            df,
            ["playing_role", "role"],
        )
        role = _sidebar_top_category(df, role_col)

        batting_col = _sidebar_find_column(
            df,
            ["batting_style"],
        )
        bowling_col = _sidebar_find_column(
            df,
            ["bowling_style"],
        )

        add(
            "👑",
            "Largest role",
            role[0] if role else None,
            f"{role[1]} players" if role else "",
        )

        if batting_col:
            available = (
                df[batting_col]
                .notna()
                & (
                    df[batting_col]
                    .astype(str)
                    .str.strip()
                    != ""
                )
            ).sum()
            add(
                "🏏",
                "Batting profiles",
                f"{int(available)}/{len(df)}",
                "Players with a batting style recorded.",
            )

        if bowling_col:
            available = (
                df[bowling_col]
                .notna()
                & (
                    df[bowling_col]
                    .astype(str)
                    .str.strip()
                    != ""
                )
            ).sum()
            add(
                "⚾",
                "Bowling profiles",
                f"{int(available)}/{len(df)}",
                "Players with a bowling style recorded.",
            )

    elif query_number == "Q2":
        winner_col = _sidebar_find_column(
            df,
            ["winning_team"],
        )
        venue_col = _sidebar_find_column(
            df,
            ["venue_name", "venue"],
        )
        format_col = _sidebar_find_column(
            df,
            ["match_type", "format"],
        )

        completed = 0
        if winner_col:
            completed = (
                df[winner_col].notna()
                & (
                    df[winner_col]
                    .astype(str)
                    .str.strip()
                    != ""
                )
                & (
                    df[winner_col]
                    .astype(str)
                    .str.lower()
                    != "none"
                )
            ).sum()

        add(
            "🏆",
            "Completed",
            f"{int(completed)}/{len(df)}",
            "Matches with a recorded winner.",
        )

        venue = _sidebar_top_category(df, venue_col)
        add(
            "🏟️",
            "Busiest venue",
            venue[0] if venue else None,
            f"{venue[1]} matches" if venue else "",
        )

        match_format = _sidebar_top_category(df, format_col)
        add(
            "🏏",
            "Most common format",
            match_format[0] if match_format else None,
            f"{match_format[1]} matches" if match_format else "",
        )

    elif query_number == "Q3":
        result = _sidebar_top_numeric(
            df,
            ["runs_scored", "runs", "total_runs"],
            ["player_name", "player"],
            "Run leader",
            suffix="runs",
        )
        if result:
            add(result[0], result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["batting_average", "average", "avg"],
            ["player_name", "player"],
            "Best average",
        )
        if result:
            add("📈", result[1], result[2], "Highest batting average in the result.")

        result = _sidebar_top_numeric(
            df,
            ["hundreds", "centuries", "100s"],
            ["player_name", "player"],
            "Century leader",
        )
        if result:
            add("💯", result[1], result[2], "Most hundreds in the result.")

    elif query_number == "Q4":
        result = _sidebar_top_numeric(
            df,
            ["matches_played", "match_count", "matches", "total_matches"],
            ["venue_name", "venue"],
            "Top venue",
            suffix="matches",
        )
        if result:
            add("🏟️", result[1], result[2])
        else:
            venue_col = _sidebar_find_column(df, ["venue_name", "venue"])
            venue = _sidebar_top_category(df, venue_col)
            add(
                "🏟️",
                "Top venue",
                venue[0] if venue else None,
                f"{venue[1]} records" if venue else "",
            )

        city_col = _sidebar_find_column(df, ["city"])
        city = _sidebar_top_category(df, city_col)
        add(
            "📍",
            "Top city",
            city[0] if city else None,
            f"{city[1]} records" if city else "",
        )

    elif query_number == "Q5":
        result = _sidebar_top_numeric(
            df,
            ["wins", "win_count", "total_wins", "matches_won"],
            ["team_name", "team", "winning_team"],
            "Win leader",
            suffix="wins",
        )
        if result:
            add("🏆", result[1], result[2])

        team_col = _sidebar_find_column(
            df,
            ["team_name", "team", "winning_team"],
        )
        add(
            "👥",
            "Teams ranked",
            df[team_col].nunique() if team_col else None,
            "Distinct teams in the result.",
        )

    elif query_number == "Q6":
        role_col = _sidebar_find_column(df, ["playing_role", "role"])
        role = _sidebar_top_category(df, role_col)
        add(
            "👑",
            "Dominant role",
            role[0] if role else None,
            f"{role[1]} players" if role else "",
        )

        result = _sidebar_top_numeric(
            df,
            ["total_matches", "matches", "match_count"],
            ["player_name", "player"],
            "Most experienced",
            suffix="matches",
        )
        if result:
            add("🏏", result[1], result[2])

    elif query_number == "Q7":
        result = _sidebar_top_numeric(
            df,
            ["runs_scored", "runs", "total_runs", "runs_2026"],
            ["player_name", "player"],
            "Batting leader",
            suffix="runs",
        )
        if result:
            add("🏏", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["batting_average", "avg_runs", "average"],
            ["player_name", "player"],
            "Best average",
        )
        if result:
            add("📈", result[1], result[2])

    elif query_number == "Q8":
        result = _sidebar_top_numeric(
            df,
            ["matches", "match_count", "total_matches"],
            ["series_name", "series", "description"],
            "Biggest series",
            suffix="matches",
        )
        if result:
            add("🏆", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["runs", "total_runs", "runs_scored"],
            ["series_name", "series", "description"],
            "Highest runs",
            suffix="runs",
        )
        if result:
            add("🏏", result[1], result[2])

    elif query_number == "Q9":
        result = _sidebar_top_numeric(
            df,
            ["overall_score", "score", "performance_score", "runs_scored"],
            ["player_name", "player"],
            "Top all-rounder",
        )
        if result:
            add("🏆", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["wickets", "wickets_taken", "total_wickets"],
            ["player_name", "player"],
            "Most wickets",
        )
        if result:
            add("⚾", result[1], result[2])

    elif query_number == "Q10":
        result = _sidebar_top_numeric(
            df,
            ["runs", "runs_scored", "total_runs", "avg_runs", "performance_score"],
            ["player_name", "team_name", "team", "player"],
            "Top recent performer",
        )
        if result:
            add("🔥", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["win_percentage", "win_pct", "winning_percentage"],
            ["team_name", "team"],
            "Best win rate",
            suffix="%",
        )
        if result:
            add("🏆", result[1], result[2])

    elif query_number == "Q12":
        result = _sidebar_top_numeric(
            df,
            ["home_win_percentage", "home_win_pct"],
            ["team_name", "team"],
            "Best home rate",
            suffix="%",
        )
        if result:
            add("🏠", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["away_win_percentage", "away_win_pct"],
            ["team_name", "team"],
            "Best away rate",
            suffix="%",
        )
        if result:
            add("✈️", result[1], result[2])

    elif query_number == "Q13" or query_number == "Q24":
        result = _sidebar_top_numeric(
            df,
            [
                "partnership_runs",
                "partnership_score",
                "runs",
                "average_partnership",
                "avg_partnership",
                "highest_partnership",
            ],
            [
                "partnership",
                "pair",
                "batting_pair",
                "player_pair",
                "player_name",
            ],
            "Top partnership",
            suffix="runs",
        )
        if result:
            add("🤝", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["success_rate", "win_percentage", "win_pct"],
            [
                "partnership",
                "pair",
                "batting_pair",
                "player_pair",
            ],
            "Best success rate",
            suffix="%",
        )
        if result:
            add("📈", result[1], result[2])

    elif query_number == "Q14":
        result = _sidebar_top_numeric(
            df,
            ["wickets", "wickets_taken", "total_wickets"],
            ["player_name", "player", "bowler"],
            "Wicket leader",
            suffix="wickets",
        )
        if result:
            add("⚾", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["economy", "economy_rate", "avg_economy"],
            ["player_name", "player", "bowler"],
            "Best economy",
            mode="min",
        )
        if result:
            add("🎯", result[1], result[2])

    elif query_number == "Q15":
        result = _sidebar_top_numeric(
            df,
            ["margin", "victory_margin", "runs_margin", "wickets_margin"],
            ["winning_team", "team_name", "team"],
            "Largest close-match margin",
        )
        if result:
            add("⚔️", result[1], result[2])

        winner_col = _sidebar_find_column(
            df,
            ["winning_team", "winner", "team_name"],
        )
        winner = _sidebar_top_category(df, winner_col)
        add(
            "🏆",
            "Most frequent winner",
            winner[0] if winner else None,
            f"{winner[1]} wins" if winner else "",
        )

    elif query_number == "Q16":
        result = _sidebar_top_numeric(
            df,
            ["run_growth", "growth", "avg_runs", "runs_2026"],
            ["player_name", "player"],
            "Growth leader",
        )
        if result:
            add("📈", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["sr_2026", "strike_rate", "avg_strike_rate"],
            ["player_name", "player"],
            "Strike-rate leader",
        )
        if result:
            add("⚡", result[1], result[2])

        trend_col = _sidebar_find_column(df, ["trend"])
        trend = _sidebar_top_category(df, trend_col)
        add(
            "🔥",
            "Most common trend",
            trend[0] if trend else None,
            f"{trend[1]} players" if trend else "",
        )

    elif query_number == "Q17":
        result = _sidebar_top_numeric(
            df,
            ["win_percentage", "win_pct", "toss_win_percentage"],
            ["team_name", "team"],
            "Best toss advantage",
            suffix="%",
        )
        if result:
            add("🪙", result[1], result[2])

        toss_col = _sidebar_find_column(
            df,
            ["toss_decision", "toss_result", "decision"],
        )
        toss = _sidebar_top_category(df, toss_col)
        add(
            "🪙",
            "Most common toss choice",
            toss[0] if toss else None,
            f"{toss[1]} matches" if toss else "",
        )

    elif query_number == "Q19":
        result = _sidebar_top_numeric(
            df,
            ["consistency_score"],
            ["player_name", "player"],
            "Consistency leader",
        )
        if result:
            add("🎯", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["avg_runs", "average_runs"],
            ["player_name", "player"],
            "Highest average",
        )
        if result:
            add("🏏", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["stddev_runs", "standard_deviation"],
            ["player_name", "player"],
            "Lowest variation",
            mode="min",
        )
        if result:
            add("📉", result[1], result[2])

    elif query_number == "Q20":
        result = _sidebar_top_numeric(
            df,
            ["total_matches"],
            ["player_name", "player"],
            "Most experienced",
            suffix="matches",
        )
        if result:
            add("🏏", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["test_avg"],
            ["player_name", "player"],
            "Best Test average",
        )
        if result:
            add("🟥", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["odi_avg"],
            ["player_name", "player"],
            "Best ODI average",
        )
        if result:
            add("🟦", result[1], result[2])

    elif query_number == "Q21":
        result = _sidebar_top_numeric(
            df,
            ["score", "performance_score", "weighted_score"],
            ["player_name", "player"],
            "Performance leader",
        )
        if result:
            add("🏆", result[1], result[2])

        format_col = _sidebar_find_column(
            df,
            ["format"],
        )
        formats = (
            df[format_col].nunique()
            if format_col
            else None
        )
        add(
            "🏏",
            "Formats ranked",
            formats,
            "Distinct formats represented.",
        )

    elif query_number == "Q22":
        team_a_col = _sidebar_find_column(
            df,
            ["team_a"],
        )
        team_b_col = _sidebar_find_column(
            df,
            ["team_b"],
        )
        pct_a_col = _sidebar_find_column(
            df,
            ["team_a_win_percentage", "team_a_win_pct"],
        )
        pct_b_col = _sidebar_find_column(
            df,
            ["team_b_win_percentage", "team_b_win_pct"],
        )

        if team_a_col and team_b_col and pct_a_col and pct_b_col:
            row = df.iloc[0]
            pct_a = pd.to_numeric(
                row[pct_a_col],
                errors="coerce",
            )
            pct_b = pd.to_numeric(
                row[pct_b_col],
                errors="coerce",
            )

            if pd.notna(pct_a) and pd.notna(pct_b):
                if pct_a >= pct_b:
                    add(
                        "🏆",
                        "H2H edge",
                        _sidebar_clean(row[team_a_col]),
                        f"{_sidebar_number(pct_a)}% historical win share.",
                    )
                else:
                    add(
                        "🏆",
                        "H2H edge",
                        _sidebar_clean(row[team_b_col]),
                        f"{_sidebar_number(pct_b)}% historical win share.",
                    )

        total_col = _sidebar_find_column(
            df,
            ["total_matches", "matches"],
        )
        if total_col:
            value = pd.to_numeric(
                df[total_col].iloc[0],
                errors="coerce",
            )
            if pd.notna(value):
                add(
                    "⚔️",
                    "Meetings",
                    _sidebar_number(value),
                    "Qualifying head-to-head meetings.",
                )

    elif query_number == "Q23":
        result = _sidebar_top_numeric(
            df,
            ["form_score", "recent_form", "form_rating", "score"],
            ["player_name", "player", "team_name", "team"],
            "Form leader",
        )
        if result:
            add("🔥", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["momentum", "momentum_score", "growth", "trend_score"],
            ["player_name", "player", "team_name", "team"],
            "Momentum leader",
        )
        if result:
            add("📈", result[1], result[2])

    elif query_number == "Q25":
        result = _sidebar_top_numeric(
            df,
            ["run_growth", "growth", "career_growth", "avg_runs"],
            ["player_name", "player"],
            "Growth leader",
        )
        if result:
            add("🚀", result[1], result[2])

        result = _sidebar_top_numeric(
            df,
            ["sr_2026", "strike_rate", "avg_strike_rate"],
            ["player_name", "player"],
            "Strike-rate leader",
        )
        if result:
            add("⚡", result[1], result[2])

    # Generic fallback for Q11/Q18 and any result where a specialized
    # metric was not available. These are still calculated from real data.
    if len(insights) < 4:
        numeric_candidates = []

        for column in df.columns:
            numeric_values = pd.to_numeric(
                df[column],
                errors="coerce",
            )
            if numeric_values.notna().sum() >= 2:
                numeric_candidates.append(
                    (column, numeric_values)
                )

        # Prefer columns whose names indicate meaningful cricket metrics.
        priority_words = [
            "runs",
            "score",
            "wins",
            "wickets",
            "average",
            "avg",
            "percentage",
            "pct",
            "rate",
            "margin",
            "matches",
            "count",
            "growth",
        ]

        numeric_candidates.sort(
            key=lambda item: (
                -sum(
                    word in str(item[0]).lower()
                    for word in priority_words
                ),
                str(item[0]).lower(),
            )
        )

        for column, values in numeric_candidates:
            if len(insights) >= 4:
                break

            if any(
                str(item[1]).lower() == str(column).lower()
                for item in insights
            ):
                continue

            maximum = values.max()
            minimum = values.min()

            if pd.isna(maximum):
                continue

            add(
                "📌",
                str(column).replace("_", " "),
                _sidebar_number(maximum),
                "Highest value in the returned result.",
            )

    # Final fallback if the query only returned categorical data.
    if len(insights) < 4:
        for column in df.columns:
            if len(insights) >= 4:
                break

            category = _sidebar_top_category(df, column)

            if not category:
                continue

            add(
                "🔎",
                str(column).replace("_", " "),
                category[0],
                f"{category[1]} records",
            )

    return title, insights[:4]


# Initialize query state before rendering the dynamic sidebar.
if "sql_query_result" not in st.session_state:
    st.session_state["sql_query_result"] = None

if "sql_query_choice" not in st.session_state:
    st.session_state["sql_query_choice"] = None


choice = st.selectbox(
    "Choose a query",
    list(QUERIES.keys())
)

sql = QUERIES[choice]

with st.expander("View SQL"):
    st.code(sql, language="sql")

run_clicked = st.button("Run query", type="primary")

if run_clicked:
    st.session_state["sql_query_result"] = run_query(sql)

    if choice.startswith("Q22:"):
        st.session_state["q22_venue_result"] = run_query(
            Q22_VENUE_PERFORMANCE
        )

    # The sidebar is updated only after the SQL has actually executed.
    st.session_state["sql_query_choice"] = choice


# Render actual query insights in the sidebar.
#
# IMPORTANT:
# Do not render the insight cards as HTML strings. Streamlit can display
# multiline HTML as a code block depending on the Markdown renderer/version.
# The sidebar therefore uses native Streamlit components for the cards.

executed_query = st.session_state.get("sql_query_choice")
executed_result = st.session_state.get("sql_query_result")

sidebar_title, sidebar_insights = _sidebar_build_insights(
    executed_query,
    executed_result,
)

with st.sidebar:
    st.markdown(f"### {sidebar_title}")
    st.caption("FACTS FROM LAST EXECUTED QUERY")

    if executed_query and executed_result is not None:
        if sidebar_insights:
            for index, (icon, label, value, detail) in enumerate(sidebar_insights):
                with st.container(border=True):
                    top_col, value_col = st.columns([0.22, 0.78])

                    with top_col:
                        st.markdown(
                            f"<div class='sql-insight-icon'>{html.escape(str(icon))}</div>",
                            unsafe_allow_html=True,
                        )

                    with value_col:
                        st.markdown(
                            f"<div class='sql-insight-label'>{html.escape(str(label))}</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<div class='sql-insight-value'>{html.escape(str(value))}</div>",
                            unsafe_allow_html=True,
                        )

                    if detail:
                        st.caption(str(detail))

        st.caption(f"Last executed: {executed_query}")

    else:
        with st.container(border=True):
            st.markdown("**Run a query to see real insights here.**")
            st.caption(
                "This panel uses the values returned by the SQL result."
            )

    st.caption("CRICBUZZ LIVESTATS")


if (
    st.session_state["sql_query_result"] is not None
    and st.session_state["sql_query_choice"] == choice
):

        try:
            df = st.session_state["sql_query_result"].copy()

            if df.empty:

                st.info(
                    "Query ran successfully but returned no rows — "
                    "load some data via the scripts in data/ first."
                )


            elif choice.startswith("Q1:"):

                st.subheader("🇮🇳 India Squad")

                df = df.copy()

                df["batting_style"] = df["batting_style"].fillna("N/A")
                df["bowling_style"] = df["bowling_style"].fillna("N/A")

                total_players = len(df)

                role_counts = (
                    df["playing_role"]
                    .value_counts()
                )

                batting_available = (
                    df["batting_style"] != "N/A"
                ).sum()

                bowling_available = (
                    df["bowling_style"] != "N/A"
                ).sum()

                role_icons = {
                    "Batsman": "🏏",
                    "Bowler": "⚾",
                    "All-rounder": "🏏⚾",
                    "Wicket-keeper": "🧤"
                }

                indian_flag = get_indian_flag_html()

                st.html(
                    f"""
                    <div style="
                        padding:28px;
                        border-radius:18px;
                        border:1px solid #d9d9d9;
                        text-align:center;
                        margin:5px 0 20px 0;
                        background:linear-gradient(
                            135deg,
                            rgba(255,153,51,0.16),
                            rgba(255,255,255,0.04)
                        );
                    ">
                        <div style="
                            font-size:48px;
                            line-height:1.2;
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            gap:12px;
                        ">
                            {indian_flag}

                            <span>
                                IN
                            </span>
                        </div>

                        <div style="
                            font-size:14px;
                            letter-spacing:2px;
                            opacity:0.7;
                            margin-top:8px;
                        ">
                            INDIA SQUAD
                        </div>

                        <div style="
                            font-size:34px;
                            font-weight:700;
                            margin:8px 0;
                        ">
                            {total_players} Players
                        </div>

                        <div style="
                            font-size:15px;
                            opacity:0.75;
                        ">
                            Active roster
                        </div>
                    </div>
                    """
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "👥 Squad",
                        total_players
                    )

                with col2:
                    st.metric(
                        "🏏 Batsmen",
                        int(role_counts.get("Batsman", 0))
                    )

                with col3:
                    st.metric(
                        "🏏⚾ All-rounders",
                        int(role_counts.get("All-rounder", 0))
                    )

                with col4:
                    st.metric(
                        "⚾ Bowlers",
                        int(role_counts.get("Bowler", 0))
                    )

                st.divider()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "🧤 Wicketkeepers",
                        int(
                            role_counts.get(
                                "Wicket-keeper",
                                0
                            )
                        )
                    )

                with col2:
                    st.metric(
                        "🏏 Bat Profiles",
                        f"{batting_available}/{total_players}"
                    )

                with col3:
                    st.metric(
                        "⚾ Bowl Profiles",
                        f"{bowling_available}/{total_players}"
                    )

                st.divider()

                st.markdown("### 🧩 Squad Roles")

                role_options = [
                    "All",
                    "Batsman",
                    "All-rounder",
                    "Wicket-keeper",
                    "Bowler"
                ]

                selected_role = st.radio(
                    "Filter by role",
                    role_options,
                    horizontal=True
                )

                display_df = (
                    df
                    if selected_role == "All"
                    else df[
                        df["playing_role"] == selected_role
                    ]
                ).copy()

                if selected_role == "All":

                    st.markdown("### 🏆 Squad Breakdown")

                    role_order = [
                        ("Batsman", "🏏"),
                        ("All-rounder", "🏏⚾"),
                        ("Wicket-keeper", "🧤"),
                        ("Bowler", "⚾")
                    ]

                    cols = st.columns(4)

                    for col, (role, icon) in zip(
                        cols,
                        role_order
                    ):

                        count = int(
                            role_counts.get(role, 0)
                        )

                        percentage = (
                            count / total_players * 100
                            if total_players
                            else 0
                        )

                        with col:

                            st.html(
                                f"""
                                <div style="
                                    padding:18px;
                                    border:1px solid #d9d9d9;
                                    border-radius:14px;
                                    text-align:center;
                                    min-height:145px;
                                ">
                                    <div style="
                                        font-size:32px;
                                    ">
                                        {icon}
                                    </div>

                                    <div style="
                                        font-size:16px;
                                        font-weight:600;
                                        margin-top:8px;
                                    ">
                                        {role}
                                    </div>

                                    <div style="
                                        font-size:28px;
                                        font-weight:700;
                                        margin:6px 0;
                                    ">
                                        {count}
                                    </div>

                                    <div style="
                                        opacity:0.7;
                                        font-size:13px;
                                    ">
                                        {percentage:.1f}% of squad
                                    </div>
                                </div>
                                """
                            )

                    st.divider()

                st.markdown(
                    f"### 👤 {selected_role} Players"
                )

                st.caption(
                    f"{len(display_df)} players"
                )

                if not PLAYER_IMAGE_DIR.exists():
                    st.warning(
                        "Player image folder was not found: "
                        f"{PLAYER_IMAGE_DIR}"
                    )

                for start in range(
                    0,
                    len(display_df),
                    3
                ):

                    card_rows = display_df.iloc[
                        start:start + 3
                    ]

                    cols = st.columns(3)

                    for col, (_, player) in zip(
                        cols,
                        card_rows.iterrows()
                    ):

                        role = player["playing_role"]

                        icon = role_icons.get(
                            role,
                            "👤"
                        )

                        player_name_raw = str(
                            player["player_name"]
                        ).strip()

                        player_name = html.escape(
                            player_name_raw
                        )

                        player_image = get_player_image_html(
                            player_name_raw
                        )

                        with col:

                            st.html(
                                f"""
                                <div style="
                                    padding:20px;
                                    border:1px solid #d9d9d9;
                                    border-radius:14px;
                                    margin-bottom:15px;
                                    min-height:300px;
                                    box-sizing:border-box;
                                    background:rgba(0,0,0,0.08);
                                ">
                                    <div style="
                                        display:flex;
                                        flex-direction:column;
                                        align-items:flex-start;
                                    ">
                                        {player_image}
                                    </div>

                                    <div style="
                                        font-size:19px;
                                        font-weight:700;
                                        margin:4px 0 4px 0;
                                    ">
                                        {player_name}
                                    </div>

                                    <div style="
                                        font-size:13px;
                                        opacity:0.7;
                                        margin-bottom:14px;
                                    ">
                                        {icon} {html.escape(str(role))}
                                    </div>

                                    <div style="
                                        font-size:13px;
                                        margin:6px 0;
                                    ">
                                        🏏 <b>Batting:</b>
                                        {html.escape(str(player['batting_style']))}
                                    </div>

                                    <div style="
                                        font-size:13px;
                                        margin:6px 0;
                                    ">
                                        ⚾ <b>Bowling:</b>
                                        {html.escape(str(player['bowling_style']))}
                                    </div>
                                </div>
                                """
                            )

                st.divider()

                st.markdown("### 📋 Complete Squad")

                table_df = display_df[
                    [
                        "player_name",
                        "playing_role",
                        "batting_style",
                        "bowling_style"
                    ]
                ].copy()

                table_df.columns = [
                    "Player",
                    "Playing Role",
                    "Batting Style",
                    "Bowling Style"
                ]

                st.dataframe(
                    table_df,
                    use_container_width=True,
                    hide_index=True,
                    height=600
                )

                st.caption(
                    "N/A means Cricbuzz did not supply a bowling "
                    "style for that player."
                )

                st.download_button(
                    "Download results as CSV",
                    df.to_csv(index=False),
                    file_name="Q1.csv",
                    mime="text/csv"
                )


            elif choice.startswith("Q2:"):

                st.subheader("🏟️ 30-Day Match Arena")

                st.caption(
                    "Matches played during the last 30 days • "
                    "scores from the local database scorecards"
                )

                df = df.copy()

                df["match_date"] = pd.to_datetime(
                    df["match_date"],
                    errors="coerce"
                )

                df = df.dropna(
                    subset=["match_date"]
                ).sort_values(
                    "match_date",
                    ascending=False
                ).reset_index(drop=True)

                total_matches = len(df)

                total_venues = df["venue_name"].nunique()
                total_cities = df["city"].nunique()

                completed_matches = (
                    df["winning_team"].notna()
                    & (
                        df["winning_team"]
                        .astype(str)
                        .str.strip()
                        != ""
                    )
                    & (
                        df["winning_team"]
                        .astype(str)
                        .str.lower()
                        != "none"
                    )
                ).sum()

                def load_database_scorecards(match_ids):
                    """
                    Read the match-level scorecards stored in SQLite.

                    The database is the single source of truth.

                    This function does not use the Cricbuzz API cache.
                    This function does not make API calls.
                    """

                    scorecards = {}

                    clean_ids = []

                    for match_id in match_ids:

                        if pd.isna(match_id):
                            continue

                        try:
                            clean_ids.append(
                                int(match_id)
                            )
                        except (
                            TypeError,
                            ValueError
                        ):
                            continue

                    if not clean_ids:
                        return scorecards

                    # run_query() accepts only the SQL string.
                    #
                    # Therefore we do not use:
                    #
                    #     IN (?,?,?,?,...)
                    #
                    # because that would require parameter bindings.
                    #
                    # The IDs have already been normalized to integers,
                    # so they can safely be placed directly into the query.
                    match_id_list = ",".join(
                        str(match_id)
                        for match_id in clean_ids
                    )

                    score_df = run_query(
                        f"""
                        SELECT
                            match_id,
                            innings_no,
                            team_name,
                            runs,
                            wickets
                        FROM match_scorecards
                        WHERE match_id IN ({match_id_list})
                        ORDER BY match_id, innings_no
                        """
                    )

                    if score_df.empty:
                        return scorecards

                    for _, row in score_df.iterrows():

                        match_id = int(
                            row["match_id"]
                        )

                        innings_no = int(
                            row["innings_no"]
                        )

                        runs = row["runs"]
                        wickets = row["wickets"]

                        if pd.isna(runs):
                            continue

                        score_text = str(
                            int(runs)
                        )

                        if not pd.isna(wickets):
                            score_text += (
                                f"/{int(wickets)}"
                            )

                        scorecards.setdefault(
                            match_id,
                            {}
                        )[innings_no] = {
                            "team": str(
                                row["team_name"]
                            ),
                            "score": score_text,
                        }

                    return scorecards


                st.html(
                    f"""
                    <div style="
                        padding:28px;
                        border-radius:18px;
                        border:1px solid #d9d9d9;
                        text-align:center;
                        margin:5px 0 20px 0;
                        background:linear-gradient(
                            135deg,
                            rgba(34,139,230,0.14),
                            rgba(255,255,255,0.04)
                        );
                    ">
                        <div style="
                            font-size:48px;
                        ">
                            🏟️
                        </div>

                        <div style="
                            font-size:14px;
                            letter-spacing:2px;
                            opacity:0.7;
                            margin-top:8px;
                        ">
                            MATCH ARENA
                        </div>

                        <div style="
                            font-size:34px;
                            font-weight:700;
                            margin:8px 0;
                        ">
                            {total_matches} Matches
                        </div>

                        <div style="
                            font-size:15px;
                            opacity:0.75;
                        ">
                            Last 30 days
                        </div>
                    </div>
                    """
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "🏏 Matches",
                        total_matches
                    )

                with col2:
                    st.metric(
                        "🏆 Completed",
                        int(completed_matches)
                    )

                with col3:
                    st.metric(
                        "🏟️ Venues",
                        total_venues
                    )

                with col4:
                    st.metric(
                        "🌍 Cities",
                        total_cities
                    )

                st.divider()

                if "match_type" in df.columns:

                    format_counts = (
                        df["match_type"]
                        .fillna("Unknown")
                        .value_counts()
                    )

                    st.markdown(
                        "### 🏏 Match Formats"
                    )

                    format_items = (
                        format_counts
                        .head(4)
                        .index
                        .tolist()
                    )

                    cols = st.columns(
                        max(
                            len(format_items),
                            1
                        )
                    )

                    for col, format_name in zip(
                        cols,
                        format_items
                    ):

                        with col:

                            st.metric(
                                f"🏏 {format_name}",
                                int(
                                    format_counts[
                                        format_name
                                    ]
                                )
                            )

                    st.divider()

                    # Normalize format values so filtering is consistent.
                    df["_format_normalized"] = (
                        df["match_type"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.upper()
                    )

                    format_values = (
                        df.loc[
                            df["_format_normalized"] != "",
                            "_format_normalized"
                        ]
                        .drop_duplicates()
                        .tolist()
                    )

                    formats = ["All"] + sorted(format_values)

                    selected_format = st.radio(
                        "Filter by format",
                        formats,
                        horizontal=True,
                        key="q2_format_filter"
                    )

                    if selected_format == "All":
                        display_df = df.copy()
                    else:
                        display_df = df[
                            df["_format_normalized"] == selected_format
                        ].copy()

                else:

                    selected_format = "All"

                    display_df = df.copy()


                # Select exactly the 10 most recent matches.
                recent_match_ids_df = run_query(
                    """
                    SELECT
                        match_id
                    FROM matches
                    ORDER BY
                        date(match_date) DESC,
                        match_id DESC
                    LIMIT 10
                    """
                )

                recent_match_ids = (
                    recent_match_ids_df[
                        "match_id"
                    ].tolist()
                    if "match_id"
                    in recent_match_ids_df.columns
                    else []
                )


                card_df = (
                    display_df[
                        display_df["match_id"].isin(
                            recent_match_ids
                        )
                    ]
                    .copy()
                )


                card_df["match_id_order"] = (
                    card_df["match_id"]
                    .map(
                        {
                            match_id: index
                            for index, match_id
                            in enumerate(
                                recent_match_ids
                            )
                        }
                    )
                )


                card_df = (
                    card_df
                    .sort_values(
                        "match_id_order"
                    )
                    .drop(
                        columns=[
                            "match_id_order"
                        ]
                    )
                    .reset_index(
                        drop=True
                    )
                )


                # Read the corrected scorecards directly from SQLite.
                database_scorecards = (
                    load_database_scorecards(
                        card_df["match_id"].tolist()
                    )
                )


                score_map = {}


                for _, match in card_df.iterrows():

                    match_id = match.get(
                        "match_id"
                    )

                    if pd.isna(match_id):
                        continue

                    try:
                        match_id = int(
                            match_id
                        )
                    except (
                        TypeError,
                        ValueError
                    ):
                        continue

                    innings = (
                        database_scorecards.get(
                            match_id,
                            {}
                        )
                    )

                    score_map[
                        match_id
                    ] = {
                        "team1_score": innings.get(
                            1,
                            {}
                        ).get(
                            "score",
                            "—"
                        ),

                        "team2_score": innings.get(
                            2,
                            {}
                        ).get(
                            "score",
                            "—"
                        ),
                    }


                st.markdown(
                    "### 🗓️ Recent Matchday"
                )

                st.caption(
                    f"{len(card_df)} most recent matches shown"
                )


                for start in range(
                    0,
                    len(card_df),
                    3
                ):

                    card_rows = card_df.iloc[
                        start:start + 3
                    ]

                    cols = st.columns(3)


                    for col, (_, match) in zip(
                        cols,
                        card_rows.iterrows()
                    ):

                        formatted_date = (
                            match["match_date"]
                            .strftime(
                                "%d %b %Y"
                            )
                        )

                        team1 = str(
                            match.get(
                                "team1",
                                "Team 1"
                            )
                        )

                        team2 = str(
                            match.get(
                                "team2",
                                "Team 2"
                            )
                        )

                        venue = str(
                            match.get(
                                "venue_name",
                                "Venue unavailable"
                            )
                        )

                        city = str(
                            match.get(
                                "city",
                                "City unavailable"
                            )
                        )

                        match_type = str(
                            match.get(
                                "match_type",
                                "Format unavailable"
                            )
                        )

                        winner = match.get(
                            "winning_team",
                            None
                        )

                        result = match.get(
                            "result",
                            None
                        )

                        match_id = match.get(
                            "match_id",
                            None
                        )


                        try:
                            normalized_match_id = int(
                                match_id
                            )
                        except (
                            TypeError,
                            ValueError
                        ):
                            normalized_match_id = match_id


                        scores = score_map.get(
                            normalized_match_id,
                            {}
                        )


                        team1_score = scores.get(
                            "team1_score",
                            "—"
                        )

                        team2_score = scores.get(
                            "team2_score",
                            "—"
                        )


                        score_available = (
                            team1_score != "—"
                            or team2_score != "—"
                        )


                        if (
                            pd.isna(winner)
                            or str(winner).strip() == ""
                            or str(winner).lower()
                            == "none"
                        ):

                            winner_text = (
                                "Result unavailable"
                            )

                            winner_icon = "⏳"

                        else:

                            winner_text = str(
                                winner
                            )

                            winner_icon = "🏆"


                        if (
                            pd.isna(result)
                            or str(result).strip() == ""
                            or str(result).lower()
                            == "none"
                        ):

                            result_text = ""

                        else:

                            result_text = str(
                                result
                            )


                        score_note = (
                            "Scorecard from database"
                            if score_available
                            else "Score unavailable"
                        )


                        result_html = (
                            f"""
                            <div style="
                                font-size:12px;
                                margin-bottom:8px;
                                opacity:0.8;
                            ">
                                📌 {result_text}
                            </div>
                            """
                            if result_text
                            else ""
                        )


                        with col:

                            st.html(
                                f"""
                                <div style="
                                    padding:20px;
                                    border:1px solid #d9d9d9;
                                    border-radius:14px;
                                    margin-bottom:15px;
                                    min-height:330px;
                                    box-sizing:border-box;
                                ">

                                    <div style="
                                        display:flex;
                                        justify-content:space-between;
                                        align-items:center;
                                        margin-bottom:12px;
                                    ">
                                        <span style="
                                            font-size:13px;
                                            opacity:0.7;
                                        ">
                                            📅 {formatted_date}
                                        </span>

                                        <span style="
                                            font-size:22px;
                                        ">
                                            🏏
                                        </span>
                                    </div>

                                    <div style="
                                        font-size:16px;
                                        font-weight:700;
                                        line-height:1.4;
                                        margin-bottom:12px;
                                    ">
                                        {team1}

                                        <div style="
                                            font-size:12px;
                                            opacity:0.6;
                                            font-weight:500;
                                            margin:3px 0;
                                        ">
                                            VS
                                        </div>

                                        {team2}
                                    </div>

                                    <div style="
                                        display:flex;
                                        gap:10px;
                                        margin:12px 0;
                                    ">

                                        <div style="
                                            flex:1;
                                            padding:12px;
                                            border-radius:10px;
                                            border:1px solid #ddd;
                                            text-align:center;
                                        ">

                                            <div style="
                                                font-size:12px;
                                                opacity:0.65;
                                                margin-bottom:4px;
                                            ">
                                                🏏 {team1}
                                            </div>

                                            <div style="
                                                font-size:24px;
                                                font-weight:700;
                                            ">
                                                {team1_score}
                                            </div>

                                            <div style="
                                                font-size:11px;
                                                opacity:0.65;
                                            ">
                                                score
                                            </div>

                                        </div>


                                        <div style="
                                            flex:1;
                                            padding:12px;
                                            border-radius:10px;
                                            border:1px solid #ddd;
                                            text-align:center;
                                        ">

                                            <div style="
                                                font-size:12px;
                                                opacity:0.65;
                                                margin-bottom:4px;
                                            ">
                                                🏏 {team2}
                                            </div>

                                            <div style="
                                                font-size:24px;
                                                font-weight:700;
                                            ">
                                                {team2_score}
                                            </div>

                                            <div style="
                                                font-size:11px;
                                                opacity:0.65;
                                            ">
                                                score
                                            </div>

                                        </div>

                                    </div>


                                    <div style="
                                        padding:10px;
                                        border-radius:9px;
                                        background:rgba(
                                            46,
                                            204,
                                            113,
                                            0.10
                                        );
                                        margin:12px 0;
                                    ">

                                        <div style="
                                            font-size:11px;
                                            opacity:0.65;
                                            margin-bottom:3px;
                                        ">
                                            {winner_icon} WINNER
                                        </div>

                                        <div style="
                                            font-size:15px;
                                            font-weight:700;
                                        ">
                                            {winner_text}
                                        </div>

                                    </div>


                                    {result_html}


                                    <div style="
                                        font-size:12px;
                                        opacity:0.75;
                                        margin-top:8px;
                                    ">
                                        🏏 {match_type}
                                    </div>


                                    <div style="
                                        font-size:12px;
                                        opacity:0.75;
                                        margin-top:5px;
                                    ">
                                        🏟️ {venue}
                                    </div>


                                    <div style="
                                        font-size:12px;
                                        opacity:0.75;
                                        margin-top:5px;
                                    ">
                                        📍 {city}
                                    </div>


                                    <div style="
                                        font-size:10px;
                                        opacity:0.55;
                                        margin-top:7px;
                                    ">
                                        {score_note}
                                    </div>

                                </div>
                                """
                            )


                st.divider()


                # Full 30-day Match Schedule.
                #
                # IMPORTANT:
                # The database remains the source of truth.
                #
                # We do not modify display_df with score strings.
                # This prevents Pandas int64 dtype errors.


                st.markdown(
                    "### 📋 Match Schedule"
                )


                table_columns = [
                    "description",
                    "team1",
                    "team2",
                    "team1_runs",
                    "team2_runs",
                    "winning_team",
                    "result",
                    "venue_name",
                    "city",
                    "match_date"
                ]


                available_columns = [
                    column
                    for column in table_columns
                    if column in display_df.columns
                ]


                table_columns_with_id = [
                    "match_id"
                ] + available_columns


                table_columns_with_id = list(
                    dict.fromkeys(
                        table_columns_with_id
                    )
                )


                table_df = display_df[
                    [
                        column
                        for column in table_columns_with_id
                        if column in display_df.columns
                    ]
                ].copy()


                # Rank the full schedule by Team 1 runs,
                # highest score first.
                if "team1_runs" in table_df.columns:

                    table_df["_team1_runs_sort"] = pd.to_numeric(
                        table_df["team1_runs"],
                        errors="coerce"
                    )

                    table_df = (
                        table_df
                        .sort_values(
                            "_team1_runs_sort",
                            ascending=False,
                            na_position="last",
                            kind="stable"
                        )
                        .drop(
                            columns=[
                                "_team1_runs_sort"
                            ]
                        )
                    )

                # Display scores as runs/wickets.
                if (
                    "team1_runs" in table_df.columns
                    and "team1_wickets" in table_df.columns
                ):
                    table_df["team1_runs"] = table_df.apply(
                        lambda row: (
                            f"{int(row['team1_runs'])}/"
                            f"{int(row['team1_wickets'])}"
                        )
                        if pd.notna(row["team1_runs"])
                        and pd.notna(row["team1_wickets"])
                        and not (
                            int(row["team1_runs"]) == 0
                            and int(row["team1_wickets"]) == 0
                        )
                        else "—",
                        axis=1
                    )

                if (
                    "team2_runs" in table_df.columns
                    and "team2_wickets" in table_df.columns
                ):
                    table_df["team2_runs"] = table_df.apply(
                        lambda row: (
                            f"{int(row['team2_runs'])}/"
                            f"{int(row['team2_wickets'])}"
                        )
                        if pd.notna(row["team2_runs"])
                        and pd.notna(row["team2_wickets"])
                        and not (
                            int(row["team2_runs"]) == 0
                            and int(row["team2_wickets"]) == 0
                        )
                        else "—",
                        axis=1
                    )

                table_df = table_df.drop(
                    columns=[
                        "team1_wickets",
                        "team2_wickets"
                    ],
                    errors="ignore"
                )



                # match_id is used only internally.
                if "match_id" in table_df.columns:

                    table_df = table_df.drop(
                        columns=[
                            "match_id"
                        ]
                    )


                if "match_date" in table_df.columns:

                    table_df["match_date"] = (
                        table_df[
                            "match_date"
                        ]
                        .dt.strftime(
                            "%Y-%m-%d"
                        )
                    )


                table_df.columns = [
                    column
                    .replace(
                        "_",
                        " "
                    )
                    .title()
                    for column in table_df.columns
                ]


                st.dataframe(
                    table_df,
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )


                st.download_button(
                    "Download results as CSV",
                    table_df.to_csv(
                        index=False
                    ),
                    file_name="Q2.csv",
                    mime="text/csv"
                )



            elif choice.startswith("Q3:"):

                st.subheader("🏆 ODI Run Legends")

                st.caption(
                    "Top 10 ODI run scorers • Ranked by career runs • "
                    "Turn the leaderboard into a cricket hall of fame."
                )

                df = df.copy()

                # Normalize numeric columns from the database.
                for column in [
                    "runs_scored",
                    "batting_average",
                    "hundreds",
                ]:
                    if column in df.columns:
                        df[column] = pd.to_numeric(
                            df[column],
                            errors="coerce"
                        )

                df["runs_scored"] = df["runs_scored"].fillna(0)
                df["batting_average"] = (
                    df["batting_average"].fillna(0)
                )
                df["hundreds"] = df["hundreds"].fillna(0)

                df = (
                    df.sort_values(
                        "runs_scored",
                        ascending=False,
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:

                    st.info(
                        "No ODI run-scorer data is available."
                    )

                else:

                    # ------------------------------------------------
                    # Hall of Fame summary
                    # ------------------------------------------------

                    leader = df.iloc[0]

                    leader_name = html.escape(
                        str(leader["player_name"])
                    )

                    leader_runs = int(
                        leader["runs_scored"]
                    )

                    leader_average = float(
                        leader["batting_average"]
                    )

                    leader_hundreds = int(
                        leader["hundreds"]
                    )

                    total_top10_runs = int(
                        df["runs_scored"].sum()
                    )

                    best_average = float(
                        df["batting_average"].max()
                    )

                    century_leader = int(
                        df["hundreds"].max()
                    )

                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:
                                linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                            box-shadow:
                                0 8px 30px rgba(0,0,0,0.18);
                        ">

                            <div style="
                                font-size:52px;
                                line-height:1;
                            ">
                                👑
                            </div>

                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                ODI RUN KING
                            </div>

                            <div style="
                                font-size:32px;
                                font-weight:800;
                                margin:8px 0;
                            ">
                                {leader_name}
                            </div>

                            <div style="
                                font-size:24px;
                                font-weight:700;
                            ">
                                {leader_runs:,} RUNS
                            </div>

                            <div style="
                                margin-top:8px;
                                opacity:0.75;
                                font-size:14px;
                            ">
                                {leader_average:.2f} batting average
                                &nbsp; • &nbsp;
                                {leader_hundreds} centuries
                            </div>

                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:
                                        linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                "></div>
                            </div>

                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                🏅 100% RUN POWER
                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Quick stats
                    # ------------------------------------------------

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "🏏 Top 10 Runs",
                            f"{total_top10_runs:,}"
                        )

                    with col2:
                        st.metric(
                            "👑 Run Leader",
                            f"{leader_runs:,}"
                        )

                    with col3:
                        st.metric(
                            "📈 Best Average",
                            f"{best_average:.2f}"
                        )

                    with col4:
                        st.metric(
                            "💯 Most Centuries",
                            century_leader
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Podium
                    # ------------------------------------------------

                    st.markdown("### 🥇 The ODI Podium")

                    podium = df.head(3)

                    medals = ["🥇", "🥈", "🥉"]
                    podium_labels = [
                        "RUN KING",
                        "RUNNER-UP",
                        "BRONZE LEGEND",
                    ]

                    podium_cols = st.columns(
                        len(podium)
                    )

                    max_runs = max(
                        float(df["runs_scored"].max()),
                        1
                    )

                    for col, (_, player), medal, label in zip(
                        podium_cols,
                        podium.iterrows(),
                        medals,
                        podium_labels
                    ):

                        player_name = html.escape(
                            str(player["player_name"])
                        )

                        runs = int(
                            player["runs_scored"]
                        )

                        average = float(
                            player["batting_average"]
                        )

                        hundreds = int(
                            player["hundreds"]
                        )

                        power = (
                            runs / max_runs * 100
                        )

                        with col:

                            st.html(
                                f"""
                                <div style="
                                    padding:22px;
                                    border:1px solid #d9d9d9;
                                    border-radius:18px;
                                    text-align:center;
                                    min-height:225px;
                                    box-sizing:border-box;
                                ">

                                    <div style="
                                        font-size:38px;
                                    ">
                                        {medal}
                                    </div>

                                    <div style="
                                        font-size:11px;
                                        letter-spacing:2px;
                                        opacity:0.65;
                                        margin-top:4px;
                                    ">
                                        {label}
                                    </div>

                                    <div style="
                                        font-size:19px;
                                        font-weight:700;
                                        margin:9px 0;
                                    ">
                                        {player_name}
                                    </div>

                                    <div style="
                                        font-size:27px;
                                        font-weight:800;
                                    ">
                                        {runs:,}
                                    </div>

                                    <div style="
                                        font-size:12px;
                                        opacity:0.7;
                                    ">
                                        ODI runs
                                    </div>

                                    <div style="
                                        margin-top:12px;
                                        font-size:12px;
                                    ">
                                        📊 Avg {average:.2f}
                                        &nbsp; • &nbsp;
                                        💯 {hundreds} hundreds
                                    </div>

                                    <div style="
                                        margin-top:13px;
                                        height:7px;
                                        border-radius:8px;
                                        background:rgba(255,255,255,0.10);
                                        overflow:hidden;
                                    ">
                                        <div style="
                                            width:{power:.1f}%;
                                            height:100%;
                                            border-radius:8px;
                                            background:
                                                linear-gradient(
                                                    90deg,
                                                    #ffd700,
                                                    #ff9f1c
                                                );
                                        "></div>
                                    </div>

                                </div>
                                """
                            )

                    st.divider()

                    # ------------------------------------------------
                    # XP-style leaderboard
                    # ------------------------------------------------

                    st.markdown("### ⚔️ ODI Run Battle")

                    st.caption(
                        "Run Power is relative to the #1 scorer. "
                        "It is a visual ranking aid, not an official statistic."
                    )

                    for rank, (_, player) in enumerate(
                        df.iterrows(),
                        start=1
                    ):

                        player_name = html.escape(
                            str(player["player_name"])
                        )

                        runs = int(
                            player["runs_scored"]
                        )

                        average = float(
                            player["batting_average"]
                        )

                        hundreds = int(
                            player["hundreds"]
                        )

                        power = min(
                            (runs / max_runs) * 100,
                            100
                        )

                        if rank == 1:
                            rank_icon = "👑"
                            badge = "RUN KING"
                        elif rank == 2:
                            rank_icon = "🥈"
                            badge = "ELITE"
                        elif rank == 3:
                            rank_icon = "🥉"
                            badge = "ELITE"
                        elif rank <= 5:
                            rank_icon = "🔥"
                            badge = "TOP 5"
                        else:
                            rank_icon = "⚡"
                            badge = "TOP 10"

                        st.html(
                            f"""
                            <div style="
                                padding:15px 18px;
                                border:1px solid rgba(
                                    255,255,255,0.10
                                );
                                border-radius:14px;
                                margin:8px 0;
                                background:rgba(
                                    255,255,255,0.025
                                );
                            ">

                                <div style="
                                    display:flex;
                                    align-items:center;
                                    gap:14px;
                                ">

                                    <div style="
                                        width:38px;
                                        text-align:center;
                                        font-size:22px;
                                    ">
                                        {rank_icon}
                                    </div>

                                    <div style="
                                        min-width:155px;
                                    ">

                                        <div style="
                                            font-size:15px;
                                            font-weight:700;
                                        ">
                                            #{rank} {player_name}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            letter-spacing:1px;
                                            opacity:0.55;
                                            margin-top:3px;
                                        ">
                                            {badge}
                                        </div>

                                    </div>

                                    <div style="
                                        flex:1;
                                        min-width:120px;
                                    ">

                                        <div style="
                                            display:flex;
                                            justify-content:
                                                space-between;
                                            font-size:11px;
                                            margin-bottom:5px;
                                        ">
                                            <span>
                                                RUN POWER
                                            </span>

                                            <span>
                                                {power:.1f}%
                                            </span>
                                        </div>

                                        <div style="
                                            height:8px;
                                            border-radius:8px;
                                            background:
                                                rgba(
                                                    255,255,255,0.08
                                                );
                                            overflow:hidden;
                                        ">

                                            <div style="
                                                width:{power:.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>

                                        </div>

                                    </div>

                                    <div style="
                                        min-width:95px;
                                        text-align:right;
                                    ">

                                        <div style="
                                            font-size:18px;
                                            font-weight:800;
                                        ">
                                            {runs:,}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            opacity:0.55;
                                        ">
                                            RUNS
                                        </div>

                                    </div>

                                    <div style="
                                        min-width:115px;
                                        text-align:right;
                                        font-size:12px;
                                        opacity:0.8;
                                    ">
                                        📈 {average:.2f}
                                        &nbsp; • &nbsp;
                                        💯 {hundreds}
                                    </div>

                                </div>

                            </div>
                            """
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Detailed leaderboard table
                    # ------------------------------------------------

                    st.markdown("### 📋 Hall of Fame Stats")

                    table_df = df[
                        [
                            "player_name",
                            "runs_scored",
                            "batting_average",
                            "hundreds",
                        ]
                    ].copy()

                    table_df.insert(
                        0,
                        "Rank",
                        range(1, len(table_df) + 1)
                    )

                    table_df.columns = [
                        "Rank",
                        "Player",
                        "Runs",
                        "Batting Average",
                        "Centuries",
                    ]

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=430
                    )

                    st.download_button(
                        "Download results as CSV",
                        df.to_csv(index=False),
                        file_name="Q3.csv",
                        mime="text/csv"
                    )



            elif choice.startswith("Q4:"):

                st.subheader("🏟️ Cricket Stadium Hall of Fame")

                st.caption(
                    "Venues with 50,000+ capacity • Ranked by seating power • "
                    "Which stadiums rule the crowd?"
                )

                df = df.copy()

                # Normalize the capacity field from the database.
                df["capacity"] = pd.to_numeric(
                    df["capacity"],
                    errors="coerce"
                )

                df = (
                    df.dropna(subset=["capacity"])
                    .sort_values(
                        "capacity",
                        ascending=False,
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:

                    st.info(
                        "No qualifying venues were found."
                    )

                else:

                    # ------------------------------------------------
                    # Hall of Fame summary
                    # ------------------------------------------------

                    largest = df.iloc[0]

                    largest_name = html.escape(
                        str(largest["venue_name"])
                    )

                    largest_capacity = int(
                        largest["capacity"]
                    )

                    total_capacity = int(
                        df["capacity"].sum()
                    )

                    average_capacity = float(
                        df["capacity"].mean()
                    )

                    venue_count = len(df)

                    # ------------------------------------------------
                    # Champion stadium
                    # ------------------------------------------------

                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:
                                linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                            box-shadow:
                                0 8px 30px rgba(0,0,0,0.18);
                        ">

                            <div style="
                                font-size:52px;
                                line-height:1;
                            ">
                                👑
                            </div>

                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                CAPACITY KING
                            </div>

                            <div style="
                                font-size:30px;
                                font-weight:800;
                                margin:9px 0;
                            ">
                                {largest_name}
                            </div>

                            <div style="
                                font-size:26px;
                                font-weight:800;
                            ">
                                {largest_capacity:,}
                            </div>

                            <div style="
                                margin-top:5px;
                                font-size:13px;
                                opacity:0.7;
                            ">
                                seats • {largest["city"]}, {largest["country"]}
                            </div>

                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:
                                        linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                "></div>
                            </div>

                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                🏆 MAXIMUM CROWD POWER
                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Quick stats
                    # ------------------------------------------------

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "🏟️ Qualifying Venues",
                            venue_count
                        )

                    with col2:
                        st.metric(
                            "👑 Largest Capacity",
                            f"{largest_capacity:,}"
                        )

                    with col3:
                        st.metric(
                            "📊 Average Capacity",
                            f"{average_capacity:,.0f}"
                        )

                    with col4:
                        st.metric(
                            "🎟️ Total Seats",
                            f"{total_capacity:,}"
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Podium
                    # ------------------------------------------------

                    st.markdown("### 🥇 Stadium Podium")

                    podium = df.head(3)

                    medals = ["🥇", "🥈", "🥉"]
                    labels = [
                        "CAPACITY KING",
                        "RUNNER-UP",
                        "BRONZE STADIUM",
                    ]

                    podium_cols = st.columns(
                        len(podium)
                    )

                    max_capacity = max(
                        float(df["capacity"].max()),
                        1
                    )

                    for col, (_, venue), medal, label in zip(
                        podium_cols,
                        podium.iterrows(),
                        medals,
                        labels
                    ):

                        venue_name = html.escape(
                            str(venue["venue_name"])
                        )

                        city = html.escape(
                            str(venue["city"])
                        )

                        country = html.escape(
                            str(venue["country"])
                        )

                        capacity = int(
                            venue["capacity"]
                        )

                        power = (
                            capacity / max_capacity * 100
                        )

                        with col:

                            st.html(
                                f"""
                                <div style="
                                    padding:22px;
                                    border:1px solid #d9d9d9;
                                    border-radius:18px;
                                    text-align:center;
                                    min-height:225px;
                                    box-sizing:border-box;
                                ">

                                    <div style="
                                        font-size:38px;
                                    ">
                                        {medal}
                                    </div>

                                    <div style="
                                        font-size:11px;
                                        letter-spacing:2px;
                                        opacity:0.65;
                                        margin-top:4px;
                                    ">
                                        {label}
                                    </div>

                                    <div style="
                                        font-size:18px;
                                        font-weight:700;
                                        margin:9px 0;
                                    ">
                                        {venue_name}
                                    </div>

                                    <div style="
                                        font-size:25px;
                                        font-weight:800;
                                    ">
                                        {capacity:,}
                                    </div>

                                    <div style="
                                        font-size:12px;
                                        opacity:0.7;
                                    ">
                                        seats
                                    </div>

                                    <div style="
                                        margin-top:7px;
                                        font-size:11px;
                                        opacity:0.65;
                                    ">
                                        📍 {city}, {country}
                                    </div>

                                    <div style="
                                        margin-top:13px;
                                        height:7px;
                                        border-radius:8px;
                                        background:rgba(255,255,255,0.10);
                                        overflow:hidden;
                                    ">
                                        <div style="
                                            width:{power:.1f}%;
                                            height:100%;
                                            border-radius:8px;
                                            background:
                                                linear-gradient(
                                                    90deg,
                                                    #ffd700,
                                                    #ff9f1c
                                                );
                                        "></div>
                                    </div>

                                </div>
                                """
                            )

                    st.divider()

                    # ------------------------------------------------
                    # Capacity battle
                    # ------------------------------------------------

                    st.markdown("### ⚔️ Capacity Battle")

                    st.caption(
                        "Crowd Power is relative to the largest qualifying "
                        "venue. It is a visual ranking aid."
                    )

                    for rank, (_, venue) in enumerate(
                        df.iterrows(),
                        start=1
                    ):

                        venue_name = html.escape(
                            str(venue["venue_name"])
                        )

                        city = html.escape(
                            str(venue["city"])
                        )

                        capacity = int(
                            venue["capacity"]
                        )

                        power = min(
                            (capacity / max_capacity) * 100,
                            100
                        )

                        if rank == 1:
                            rank_icon = "👑"
                            badge = "CAPACITY KING"
                        elif rank == 2:
                            rank_icon = "🥈"
                            badge = "ELITE VENUE"
                        elif rank == 3:
                            rank_icon = "🥉"
                            badge = "ELITE VENUE"
                        elif rank <= 5:
                            rank_icon = "🔥"
                            badge = "TOP 5"
                        else:
                            rank_icon = "⚡"
                            badge = "50K+ CLUB"

                        st.html(
                            f"""
                            <div style="
                                padding:15px 18px;
                                border:1px solid rgba(
                                    255,255,255,0.10
                                );
                                border-radius:14px;
                                margin:8px 0;
                                background:rgba(
                                    255,255,255,0.025
                                );
                            ">

                                <div style="
                                    display:flex;
                                    align-items:center;
                                    gap:14px;
                                ">

                                    <div style="
                                        width:38px;
                                        text-align:center;
                                        font-size:22px;
                                    ">
                                        {rank_icon}
                                    </div>

                                    <div style="
                                        min-width:230px;
                                    ">

                                        <div style="
                                            font-size:15px;
                                            font-weight:700;
                                        ">
                                            #{rank} {venue_name}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            letter-spacing:1px;
                                            opacity:0.55;
                                            margin-top:3px;
                                        ">
                                            {badge}
                                        </div>

                                    </div>

                                    <div style="
                                        min-width:145px;
                                        font-size:11px;
                                        opacity:0.65;
                                    ">
                                        📍 {city}
                                    </div>

                                    <div style="
                                        flex:1;
                                        min-width:120px;
                                    ">

                                        <div style="
                                            display:flex;
                                            justify-content:
                                                space-between;
                                            font-size:11px;
                                            margin-bottom:5px;
                                        ">
                                            <span>
                                                CROWD POWER
                                            </span>

                                            <span>
                                                {power:.1f}%
                                            </span>
                                        </div>

                                        <div style="
                                            height:8px;
                                            border-radius:8px;
                                            background:
                                                rgba(
                                                    255,255,255,0.08
                                                );
                                            overflow:hidden;
                                        ">

                                            <div style="
                                                width:{power:.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>

                                        </div>

                                    </div>

                                    <div style="
                                        min-width:110px;
                                        text-align:right;
                                    ">

                                        <div style="
                                            font-size:18px;
                                            font-weight:800;
                                        ">
                                            {capacity:,}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            opacity:0.55;
                                        ">
                                            SEATS
                                        </div>

                                    </div>

                                </div>

                            </div>
                            """
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Detailed venue table
                    # ------------------------------------------------

                    st.markdown("### 📋 Stadium Hall of Fame")

                    table_df = df[
                        [
                            "venue_name",
                            "city",
                            "country",
                            "capacity",
                        ]
                    ].copy()

                    table_df.insert(
                        0,
                        "Rank",
                        range(1, len(table_df) + 1)
                    )

                    table_df["capacity"] = table_df[
                        "capacity"
                    ].astype(int)

                    table_df.columns = [
                        "Rank",
                        "Venue",
                        "City",
                        "Country",
                        "Capacity",
                    ]

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=420
                    )

                    st.download_button(
                        "Download results as CSV",
                        df.to_csv(index=False),
                        file_name="Q4.csv",
                        mime="text/csv"
                    )



            elif choice.startswith("Q5:"):

                st.subheader("🏆 The Winners' Club")

                st.caption(
                    "Explore winning teams by category and competition. "
                    "Every victory earns a place on the wall."
                )

                df = df.copy()

                # Normalize the classification fields.
                df["total_wins"] = pd.to_numeric(
                    df["total_wins"],
                    errors="coerce"
                ).fillna(0)

                df["team_name"] = (
                    df["team_name"]
                    .fillna("Unknown Team")
                    .astype(str)
                    .str.strip()
                )

                df["team_category"] = (
                    df["team_category"]
                    .fillna("Other")
                    .astype(str)
                    .str.strip()
                )

                df["competition"] = (
                    df["competition"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                df["country"] = (
                    df["country"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                df = df[
                    (df["team_name"] != "")
                    & (df["team_name"].str.lower() != "unknown")
                ].copy()

                if df.empty:

                    st.info(
                        "No winning-team data is available."
                    )

                else:

                    # ------------------------------------------------
                    # Team category filter
                    # ------------------------------------------------

                    st.markdown("### 🌍 Choose Team Category")

                    category_options = [
                        "All",
                        "International",
                        "Franchise",
                        "Domestic",
                        "Other"
                    ]

                    category_labels = {
                        "All": "🌐 All Teams",
                        "International": "🌍 International",
                        "Franchise": "🏏 Franchise",
                        "Domestic": "🏟️ Domestic",
                        "Other": "📦 Other"
                    }

                    selected_category = st.radio(
                        "Team Category",
                        category_options,
                        format_func=lambda value:
                            category_labels[value],
                        horizontal=True,
                        key="q5_team_category"
                    )

                    if selected_category == "All":

                        filtered_df = df.copy()

                    else:

                        filtered_df = df[
                            df["team_category"]
                            == selected_category
                        ].copy()

                    # ------------------------------------------------
                    # Competition filter
                    # ------------------------------------------------

                    if selected_category == "Franchise":

                        st.markdown("### 🏏 Choose Competition")

                        franchise_competitions = (
                            filtered_df["competition"]
                            .replace("", pd.NA)
                            .dropna()
                            .drop_duplicates()
                            .sort_values()
                            .tolist()
                        )

                        competition_options = (
                            ["All"] + franchise_competitions
                        )

                        selected_competition = st.radio(
                            "Franchise Competition",
                            competition_options,
                            horizontal=True,
                            key="q5_franchise_competition"
                        )

                        if selected_competition == "All":

                            filtered_df = filtered_df.copy()

                        else:

                            filtered_df = filtered_df[
                                filtered_df["competition"]
                                == selected_competition
                            ].copy()

                    else:

                        selected_competition = "All"

                    # ------------------------------------------------
                    # Ranking
                    # ------------------------------------------------

                    filtered_df = (
                        filtered_df
                        .sort_values(
                            ["total_wins", "team_name"],
                            ascending=[False, True],
                            kind="stable"
                        )
                        .reset_index(drop=True)
                    )

                    if filtered_df.empty:

                        st.info(
                            "No teams match the selected category "
                            "and competition."
                        )

                    else:

                        # ------------------------------------------------
                        # Filter summary
                        # ------------------------------------------------

                        if selected_category == "All":

                            filter_text = "All Teams"

                        elif selected_category == "Franchise":

                            if selected_competition == "All":
                                filter_text = "All Franchise Teams"
                            else:
                                filter_text = (
                                    f"{selected_competition} Teams"
                                )

                        else:

                            filter_text = (
                                f"{selected_category} Teams"
                            )

                        st.caption(
                            f"Showing {len(filtered_df)} teams • "
                            f"{filter_text}"
                        )

                        # ------------------------------------------------
                        # Leaderboard summary
                        # ------------------------------------------------

                        champion = filtered_df.iloc[0]

                        champion_name = html.escape(
                            str(champion["team_name"])
                        )

                        champion_wins = int(
                            champion["total_wins"]
                        )

                        champion_category = html.escape(
                            str(champion["team_category"])
                        )

                        champion_competition = (
                            html.escape(
                                str(champion["competition"])
                            )
                            if str(champion["competition"]).strip()
                            else "—"
                        )

                        total_wins = int(
                            filtered_df["total_wins"].sum()
                        )

                        team_count = len(filtered_df)

                        average_wins = float(
                            filtered_df["total_wins"].mean()
                        )

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid
                                    rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:
                                    linear-gradient(
                                        135deg,
                                        rgba(255,215,0,0.18),
                                        rgba(255,255,255,0.035)
                                    );
                                box-shadow:
                                    0 8px 30px rgba(0,0,0,0.18);
                            ">

                                <div style="
                                    font-size:52px;
                                    line-height:1;
                                ">
                                    👑
                                </div>

                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    WINNERS' CLUB CHAMPION
                                </div>

                                <div style="
                                    font-size:32px;
                                    font-weight:800;
                                    margin:8px 0;
                                ">
                                    {champion_name}
                                </div>

                                <div style="
                                    font-size:26px;
                                    font-weight:800;
                                ">
                                    {champion_wins:,} WINS
                                </div>

                                <div style="
                                    margin-top:7px;
                                    font-size:13px;
                                    opacity:0.7;
                                ">
                                    🏷️ {champion_category}
                                    &nbsp; • &nbsp;
                                    🏏 {champion_competition}
                                </div>

                                <div style="
                                    margin-top:8px;
                                    font-size:13px;
                                    opacity:0.7;
                                ">
                                    🏆 Most victories in this category
                                </div>

                                <div style="
                                    margin:18px auto 0 auto;
                                    max-width:650px;
                                    height:10px;
                                    border-radius:10px;
                                    background:
                                        rgba(255,255,255,0.10);
                                    overflow:hidden;
                                ">
                                    <div style="
                                        width:100%;
                                        height:100%;
                                        border-radius:10px;
                                        background:
                                            linear-gradient(
                                                90deg,
                                                #ffd700,
                                                #ff9f1c
                                            );
                                    "></div>
                                </div>

                                <div style="
                                    font-size:11px;
                                    opacity:0.6;
                                    margin-top:7px;
                                ">
                                    ⚔️ VICTORY POWER: 100%
                                </div>

                            </div>
                            """
                        )

                        # ------------------------------------------------
                        # Quick stats
                        # ------------------------------------------------

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:

                            st.metric(
                                "👑 #1 Team",
                                champion_name
                            )

                        with col2:

                            st.metric(
                                "🏆 Champion Wins",
                                f"{champion_wins:,}"
                            )

                        with col3:

                            st.metric(
                                "⚔️ Total Wins",
                                f"{total_wins:,}"
                            )

                        with col4:

                            st.metric(
                                "📊 Teams Ranked",
                                team_count
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Championship podium
                        # ------------------------------------------------

                        st.markdown(
                            "### 🥇 Championship Podium"
                        )

                        podium = filtered_df.head(3)

                        medals = ["🥇", "🥈", "🥉"]

                        labels = [
                            "CHAMPION",
                            "RUNNER-UP",
                            "BRONZE"
                        ]

                        podium_cols = st.columns(
                            len(podium)
                        )

                        max_wins = max(
                            float(
                                filtered_df["total_wins"].max()
                            ),
                            1
                        )

                        for col, (_, team), medal, label in zip(
                            podium_cols,
                            podium.iterrows(),
                            medals,
                            labels
                        ):

                            team_name = html.escape(
                                str(team["team_name"])
                            )

                            wins = int(
                                team["total_wins"]
                            )

                            competition = (
                                html.escape(
                                    str(team["competition"])
                                )
                                if str(
                                    team["competition"]
                                ).strip()
                                else ""
                            )

                            power = (
                                wins / max_wins * 100
                            )

                            with col:

                                st.html(
                                    f"""
                                    <div style="
                                        padding:22px;
                                        border:1px solid #d9d9d9;
                                        border-radius:18px;
                                        text-align:center;
                                        min-height:235px;
                                        box-sizing:border-box;
                                    ">

                                        <div style="
                                            font-size:38px;
                                        ">
                                            {medal}
                                        </div>

                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:0.65;
                                            margin-top:4px;
                                        ">
                                            {label}
                                        </div>

                                        <div style="
                                            font-size:19px;
                                            font-weight:700;
                                            margin:10px 0;
                                        ">
                                            {team_name}
                                        </div>

                                        <div style="
                                            font-size:27px;
                                            font-weight:800;
                                        ">
                                            {wins:,}
                                        </div>

                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                        ">
                                            victories
                                        </div>

                                        <div style="
                                            font-size:11px;
                                            opacity:0.6;
                                            margin-top:6px;
                                        ">
                                            {competition}
                                        </div>

                                        <div style="
                                            margin-top:14px;
                                            height:7px;
                                            border-radius:8px;
                                            background:
                                                rgba(
                                                    255,
                                                    255,
                                                    255,
                                                    0.10
                                                );
                                            overflow:hidden;
                                        ">
                                            <div style="
                                                width:{power:.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>
                                        </div>

                                    </div>
                                    """
                                )

                        st.divider()

                        # ------------------------------------------------
                        # Victory battle
                        # ------------------------------------------------

                        st.markdown("### ⚔️ Victory Battle")

                        st.caption(
                            "Victory Power is relative to the team "
                            "with the most wins in the selected view."
                        )

                        for rank, (_, team) in enumerate(
                            filtered_df.iterrows(),
                            start=1
                        ):

                            team_name = html.escape(
                                str(team["team_name"])
                            )

                            wins = int(
                                team["total_wins"]
                            )

                            competition = (
                                html.escape(
                                    str(team["competition"])
                                )
                                if str(
                                    team["competition"]
                                ).strip()
                                else "Domestic / Other"
                            )

                            power = min(
                                (wins / max_wins) * 100,
                                100
                            )

                            if rank == 1:

                                rank_icon = "👑"
                                badge = "CHAMPION"

                            elif rank == 2:

                                rank_icon = "🥈"
                                badge = "FINALIST"

                            elif rank == 3:

                                rank_icon = "🥉"
                                badge = "FINALIST"

                            elif rank <= 5:

                                rank_icon = "🔥"
                                badge = "TITLE CONTENDER"

                            elif rank <= 10:

                                rank_icon = "⚡"
                                badge = "PLAYOFF ZONE"

                            else:

                                rank_icon = "🏏"
                                badge = "WINNERS' CLUB"

                            st.html(
                                f"""
                                <div style="
                                    padding:15px 18px;
                                    border:1px solid
                                        rgba(
                                            255,
                                            255,
                                            255,
                                            0.10
                                        );
                                    border-radius:14px;
                                    margin:8px 0;
                                    background:
                                        rgba(
                                            255,
                                            255,
                                            255,
                                            0.025
                                        );
                                ">

                                    <div style="
                                        display:flex;
                                        align-items:center;
                                        gap:14px;
                                    ">

                                        <div style="
                                            width:38px;
                                            text-align:center;
                                            font-size:22px;
                                        ">
                                            {rank_icon}
                                        </div>

                                        <div style="
                                            min-width:230px;
                                        ">

                                            <div style="
                                                font-size:15px;
                                                font-weight:700;
                                            ">
                                                #{rank} {team_name}
                                            </div>

                                            <div style="
                                                font-size:10px;
                                                letter-spacing:1px;
                                                opacity:0.55;
                                                margin-top:3px;
                                            ">
                                                {badge}
                                                &nbsp; • &nbsp;
                                                {competition}
                                            </div>

                                        </div>

                                        <div style="
                                            flex:1;
                                            min-width:120px;
                                        ">

                                            <div style="
                                                display:flex;
                                                justify-content:
                                                    space-between;
                                                font-size:11px;
                                                margin-bottom:5px;
                                            ">

                                                <span>
                                                    VICTORY POWER
                                                </span>

                                                <span>
                                                    {power:.1f}%
                                                </span>

                                            </div>

                                            <div style="
                                                height:8px;
                                                border-radius:8px;
                                                background:
                                                    rgba(
                                                        255,
                                                        255,
                                                        255,
                                                        0.08
                                                    );
                                                overflow:hidden;
                                            ">

                                                <div style="
                                                    width:{power:.1f}%;
                                                    height:100%;
                                                    border-radius:8px;
                                                    background:
                                                        linear-gradient(
                                                            90deg,
                                                            #ffd700,
                                                            #ff9f1c
                                                        );
                                                "></div>

                                            </div>

                                        </div>

                                        <div style="
                                            min-width:100px;
                                            text-align:right;
                                        ">

                                            <div style="
                                                font-size:19px;
                                                font-weight:800;
                                            ">
                                                {wins:,}
                                            </div>

                                            <div style="
                                                font-size:10px;
                                                opacity:0.55;
                                            ">
                                                WINS
                                            </div>

                                        </div>

                                    </div>

                                </div>
                                """
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Win tiers
                        # ------------------------------------------------

                        st.markdown("### 🎮 Victory Tiers")

                        tier1 = int(
                            (
                                filtered_df["total_wins"] >= 500
                            ).sum()
                        )

                        tier2 = int(
                            (
                                (filtered_df["total_wins"] >= 250)
                                & (
                                    filtered_df["total_wins"] < 500
                                )
                            ).sum()
                        )

                        tier3 = int(
                            (
                                (filtered_df["total_wins"] >= 100)
                                & (
                                    filtered_df["total_wins"] < 250
                                )
                            ).sum()
                        )

                        tier4 = int(
                            (
                                filtered_df["total_wins"] < 100
                            ).sum()
                        )

                        tier_cols = st.columns(4)

                        tier_data = [
                            (
                                "👑",
                                "LEGENDS",
                                tier1,
                                "500+ wins"
                            ),
                            (
                                "🔥",
                                "ELITE",
                                tier2,
                                "250–499 wins"
                            ),
                            (
                                "⚡",
                                "CONTENDERS",
                                tier3,
                                "100–249 wins"
                            ),
                            (
                                "🏏",
                                "RISING",
                                tier4,
                                "<100 wins"
                            )
                        ]

                        for col, (
                            icon,
                            title,
                            count,
                            subtitle
                        ) in zip(
                            tier_cols,
                            tier_data
                        ):

                            with col:

                                st.html(
                                    f"""
                                    <div style="
                                        text-align:center;
                                        padding:18px 10px;
                                        border:1px solid
                                            rgba(
                                                255,
                                                255,
                                                255,
                                                0.10
                                            );
                                        border-radius:15px;
                                    ">

                                        <div style="
                                            font-size:28px;
                                        ">
                                            {icon}
                                        </div>

                                        <div style="
                                            font-size:13px;
                                            font-weight:800;
                                            margin-top:5px;
                                        ">
                                            {title}
                                        </div>

                                        <div style="
                                            font-size:24px;
                                            font-weight:800;
                                            margin-top:5px;
                                        ">
                                            {count}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            opacity:0.6;
                                        ">
                                            teams • {subtitle}
                                        </div>

                                    </div>
                                    """
                                )

                        st.divider()

                        # ------------------------------------------------
                        # Detailed leaderboard
                        # ------------------------------------------------

                        st.markdown(
                            "### 📋 Winners' Club Standings"
                        )

                        table_df = filtered_df[
                            [
                                "team_name",
                                "team_category",
                                "competition",
                                "country",
                                "total_wins"
                            ]
                        ].copy()

                        table_df.insert(
                            0,
                            "Rank",
                            range(
                                1,
                                len(table_df) + 1
                            )
                        )

                        table_df["total_wins"] = (
                            table_df["total_wins"]
                            .astype(int)
                        )

                        table_df["competition"] = (
                            table_df["competition"]
                            .replace("", "—")
                        )

                        table_df["country"] = (
                            table_df["country"]
                            .replace("", "—")
                        )

                        table_df.columns = [
                            "Rank",
                            "Team",
                            "Category",
                            "Competition",
                            "Country",
                            "Total Wins"
                        ]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                            height=500
                        )

                        st.download_button(
                            "Download results as CSV",
                            filtered_df.to_csv(
                                index=False
                            ),
                            file_name="Q5.csv",
                            mime="text/csv"
                        )


            elif choice.startswith("Q6:"):

                st.subheader("🎮 Player Role Arena")

                st.caption(
                    "Every role has a squad to defend. Explore the player "
                    "pool, compare roles, and see which position dominates."
                )

                df = df.copy()

                # Normalize the database result.
                df["player_count"] = pd.to_numeric(
                    df["player_count"],
                    errors="coerce"
                ).fillna(0).astype(int)

                df["role"] = (
                    df["role"]
                    .fillna("Unknown")
                    .astype(str)
                    .str.strip()
                )

                df = df[
                    (df["role"] != "")
                    & (df["role"].str.lower() != "unknown")
                ].copy()

                df = (
                    df.sort_values(
                        ["player_count", "role"],
                        ascending=[False, True],
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:

                    st.info(
                        "No player-role data is available."
                    )

                else:

                    # ------------------------------------------------
                    # Interactive role selector
                    # ------------------------------------------------

                    roles = df["role"].tolist()

                    if "q6_selected_role" not in st.session_state:
                        st.session_state.q6_selected_role = roles[0]

                    if (
                        st.session_state.q6_selected_role
                        not in roles
                    ):
                        st.session_state.q6_selected_role = roles[0]

                    st.markdown("### 🎯 Choose Your Role")

                    role_cols = st.columns(
                        min(len(roles), 4)
                    )

                    for index, role in enumerate(roles):

                        with role_cols[index % len(role_cols)]:

                            is_selected = (
                                role
                                == st.session_state.q6_selected_role
                            )

                            if st.button(
                                (
                                    f"🏏 {role}"
                                    if not is_selected
                                    else f"⚔️ {role}"
                                ),
                                key=f"q6_role_{index}",
                                use_container_width=True
                            ):
                                st.session_state.q6_selected_role = role
                                st.rerun()

                    selected_role = (
                        st.session_state.q6_selected_role
                    )

                    selected_row = df[
                        df["role"] == selected_role
                    ].iloc[0]

                    selected_count = int(
                        selected_row["player_count"]
                    )

                    champion = df.iloc[0]

                    champion_role = html.escape(
                        str(champion["role"])
                    )

                    champion_count = int(
                        champion["player_count"]
                    )

                    total_players = int(
                        df["player_count"].sum()
                    )

                    role_count = len(df)

                    average_players = float(
                        df["player_count"].mean()
                    )

                    selected_share = (
                        selected_count / total_players * 100
                        if total_players > 0
                        else 0
                    )

                    max_count = max(
                        int(df["player_count"].max()),
                        1
                    )

                    # ------------------------------------------------
                    # Champion card
                    # ------------------------------------------------

                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:
                                linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                            box-shadow:
                                0 8px 30px rgba(0,0,0,0.18);
                        ">

                            <div style="
                                font-size:52px;
                                line-height:1;
                            ">
                                👑
                            </div>

                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                ROLE CHAMPION
                            </div>

                            <div style="
                                font-size:32px;
                                font-weight:800;
                                margin:8px 0;
                            ">
                                {champion_role}
                            </div>

                            <div style="
                                font-size:26px;
                                font-weight:800;
                            ">
                                {champion_count:,} PLAYERS
                            </div>

                            <div style="
                                margin-top:7px;
                                font-size:13px;
                                opacity:0.7;
                            ">
                                The largest squad in the player arena
                            </div>

                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:
                                        linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                "></div>
                            </div>

                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                🏆 ARENA POWER: 100%
                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Quick stats
                    # ------------------------------------------------

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "👥 Total Players",
                            f"{total_players:,}"
                        )

                    with col2:
                        st.metric(
                            "👑 Largest Squad",
                            f"{champion_count:,}"
                        )

                    with col3:
                        st.metric(
                            "🎯 Selected Squad",
                            f"{selected_count:,}"
                        )

                    with col4:
                        st.metric(
                            "🛡️ Roles",
                            role_count
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Selected role mission card
                    # ------------------------------------------------

                    selected_name = html.escape(
                        str(selected_role)
                    )

                    st.html(
                        f"""
                        <div style="
                            padding:18px 22px;
                            border:1px solid rgba(255,255,255,0.12);
                            border-radius:16px;
                            margin-bottom:18px;
                        ">

                            <div style="
                                font-size:11px;
                                letter-spacing:2px;
                                opacity:0.6;
                            ">
                                🎯 YOUR CURRENT SQUAD
                            </div>

                            <div style="
                                display:flex;
                                justify-content:space-between;
                                align-items:center;
                                gap:20px;
                                margin-top:8px;
                                flex-wrap:wrap;
                            ">

                                <div>
                                    <div style="
                                        font-size:24px;
                                        font-weight:800;
                                    ">
                                        {selected_name}
                                    </div>

                                    <div style="
                                        font-size:12px;
                                        opacity:0.65;
                                        margin-top:4px;
                                    ">
                                        {selected_count:,} players
                                        • {selected_share:.1f}% of all
                                        players in the ranked roles
                                    </div>
                                </div>

                                <div style="
                                    font-size:14px;
                                    font-weight:700;
                                ">
                                    {'👑 CURRENT LEADER'
                                    if selected_role == champion["role"]
                                    else '⚔️ CHALLENGER MODE'}
                                </div>

                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Chart 1 — role battle
                    # ------------------------------------------------

                    st.markdown("### 📊 Role Battle")

                    chart_df = df[
                        ["role", "player_count"]
                    ].set_index("role")

                    st.bar_chart(
                        chart_df,
                        y="player_count",
                        use_container_width=True,
                        height=340
                    )

                    # ------------------------------------------------
                    # Chart 2 — share of player pool
                    # ------------------------------------------------

                    st.markdown("### 🧩 Player Pool Composition")

                    share_df = df[
                        ["role", "player_count"]
                    ].copy()

                    share_df["share"] = (
                        share_df["player_count"]
                        / total_players
                        * 100
                        if total_players > 0
                        else 0
                    )

                    share_chart = share_df[
                        ["role", "share"]
                    ].set_index("role")

                    st.bar_chart(
                        share_chart,
                        y="share",
                        use_container_width=True,
                        height=300
                    )

                    st.caption(
                        "Share represents the percentage of players "
                        "across the displayed roles."
                    )

                    st.divider()

                    # ------------------------------------------------
                    # XP leaderboard
                    # ------------------------------------------------

                    st.markdown("### ⚔️ Role XP Leaderboard")

                    st.caption(
                        "Squad Power is relative to the largest role."
                    )

                    for rank, (_, role_row) in enumerate(
                        df.iterrows(),
                        start=1
                    ):

                        role_name = html.escape(
                            str(role_row["role"])
                        )

                        count = int(
                            role_row["player_count"]
                        )

                        power = min(
                            count / max_count * 100,
                            100
                        )

                        if rank == 1:
                            rank_icon = "👑"
                            badge = "BOSS CLASS"
                        elif rank == 2:
                            rank_icon = "🥈"
                            badge = "ELITE CLASS"
                        elif rank == 3:
                            rank_icon = "🥉"
                            badge = "ELITE CLASS"
                        else:
                            rank_icon = "⚡"
                            badge = "ACTIVE CLASS"

                        st.html(
                            f"""
                            <div style="
                                padding:15px 18px;
                                border:1px solid rgba(
                                    255,255,255,0.10
                                );
                                border-radius:14px;
                                margin:8px 0;
                                background:rgba(
                                    255,255,255,0.025
                                );
                            ">

                                <div style="
                                    display:flex;
                                    align-items:center;
                                    gap:14px;
                                ">

                                    <div style="
                                        width:38px;
                                        text-align:center;
                                        font-size:22px;
                                    ">
                                        {rank_icon}
                                    </div>

                                    <div style="
                                        min-width:155px;
                                    ">

                                        <div style="
                                            font-size:15px;
                                            font-weight:700;
                                        ">
                                            #{rank} {role_name}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            letter-spacing:1px;
                                            opacity:0.55;
                                            margin-top:3px;
                                        ">
                                            {badge}
                                        </div>

                                    </div>

                                    <div style="
                                        flex:1;
                                        min-width:120px;
                                    ">

                                        <div style="
                                            display:flex;
                                            justify-content:
                                                space-between;
                                            font-size:11px;
                                            margin-bottom:5px;
                                        ">
                                            <span>
                                                SQUAD POWER
                                            </span>

                                            <span>
                                                {power:.1f}%
                                            </span>
                                        </div>

                                        <div style="
                                            height:8px;
                                            border-radius:8px;
                                            background:
                                                rgba(
                                                    255,255,255,0.08
                                                );
                                            overflow:hidden;
                                        ">

                                            <div style="
                                                width:{power:.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>

                                        </div>

                                    </div>

                                    <div style="
                                        min-width:100px;
                                        text-align:right;
                                    ">

                                        <div style="
                                            font-size:19px;
                                            font-weight:800;
                                        ">
                                            {count:,}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            opacity:0.55;
                                        ">
                                            PLAYERS
                                        </div>

                                    </div>

                                </div>

                            </div>
                            """
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Detailed standings
                    # ------------------------------------------------

                    st.markdown("### 📋 Role Arena Standings")

                    table_df = df[
                        ["role", "player_count"]
                    ].copy()

                    table_df.insert(
                        0,
                        "Rank",
                        range(1, len(table_df) + 1)
                    )

                    table_df.columns = [
                        "Rank",
                        "Role",
                        "Players",
                    ]

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=300
                    )

                    st.download_button(
                        "Download results as CSV",
                        df.to_csv(index=False),
                        file_name="Q6.csv",
                        mime="text/csv"
                    )



            elif choice.startswith("Q7:"):

                st.subheader("🔥 The Ultimate Batting Bosses")

                st.caption(
                    "Highest individual batting score by format • "
                    "Three formats, three records, one scoring throne."
                )

                df = df.copy()

                # Normalize the database result.
                df["highest_score"] = pd.to_numeric(
                    df["highest_score"],
                    errors="coerce"
                )

                df["format"] = (
                    df["format"]
                    .fillna("Unknown")
                    .astype(str)
                    .str.strip()
                )

                df = df.dropna(
                    subset=["highest_score"]
                ).copy()

                df = df[
                    (df["format"] != "")
                    & (df["format"].str.lower() != "unknown")
                ].copy()

                df["highest_score"] = (
                    df["highest_score"].astype(int)
                )

                # Keep one record per format at the highest score.
                df = (
                    df.sort_values(
                        ["highest_score", "format"],
                        ascending=[False, True],
                        kind="stable"
                    )
                    .drop_duplicates(
                        subset=["format"],
                        keep="first"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:

                    st.info(
                        "No batting-score data is available."
                    )

                else:

                    # ------------------------------------------------
                    # Interactive format selector
                    # ------------------------------------------------

                    formats = df["format"].tolist()

                    if "q7_selected_format" not in st.session_state:
                        st.session_state.q7_selected_format = formats[0]

                    if (
                        st.session_state.q7_selected_format
                        not in formats
                    ):
                        st.session_state.q7_selected_format = formats[0]

                    st.markdown("### 🎯 Pick a Format")

                    format_cols = st.columns(
                        min(len(formats), 3)
                    )

                    for index, fmt in enumerate(formats):

                        with format_cols[index % len(format_cols)]:

                            is_selected = (
                                fmt
                                == st.session_state.q7_selected_format
                            )

                            if st.button(
                                (
                                    f"🏏 {fmt}"
                                    if not is_selected
                                    else f"👑 {fmt}"
                                ),
                                key=f"q7_format_{index}",
                                use_container_width=True
                            ):
                                st.session_state.q7_selected_format = fmt
                                st.rerun()

                    selected_format = (
                        st.session_state.q7_selected_format
                    )

                    selected_row = df[
                        df["format"] == selected_format
                    ].iloc[0]

                    selected_score = int(
                        selected_row["highest_score"]
                    )

                    selected_name = html.escape(
                        str(selected_row["player_name"])
                    )

                    champion = df.iloc[0]

                    champion_score = int(
                        champion["highest_score"]
                    )

                    champion_name = html.escape(
                        str(champion["player_name"])
                    )

                    champion_format = html.escape(
                        str(champion["format"])
                    )

                    average_record = float(
                        df["highest_score"].mean()
                    )

                    # ------------------------------------------------
                    # Global champion card
                    # ------------------------------------------------

                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:
                                linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                            box-shadow:
                                0 8px 30px rgba(0,0,0,0.18);
                        ">

                            <div style="
                                font-size:52px;
                                line-height:1;
                            ">
                                👑
                            </div>

                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                BATTING BOSS
                            </div>

                            <div style="
                                font-size:32px;
                                font-weight:800;
                                margin:8px 0;
                            ">
                                {champion_name}
                            </div>

                            <div style="
                                font-size:27px;
                                font-weight:800;
                            ">
                                {champion_score:,}*
                            </div>

                            <div style="
                                margin-top:7px;
                                font-size:13px;
                                opacity:0.7;
                            ">
                                Highest record • {champion_format}
                            </div>

                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:
                                        linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                "></div>
                            </div>

                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                🏏 SCORE POWER: 100%
                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Selected format challenge
                    # ------------------------------------------------

                    selected_format_html = html.escape(
                        str(selected_format)
                    )

                    selected_power = min(
                        (
                            selected_score
                            / max(champion_score, 1)
                        ) * 100,
                        100
                    )

                    st.html(
                        f"""
                        <div style="
                            padding:18px 22px;
                            border:1px solid rgba(255,255,255,0.12);
                            border-radius:16px;
                            margin-bottom:18px;
                        ">

                            <div style="
                                font-size:11px;
                                letter-spacing:2px;
                                opacity:0.6;
                            ">
                                🎮 CURRENT CHALLENGE
                            </div>

                            <div style="
                                display:flex;
                                justify-content:space-between;
                                align-items:center;
                                gap:20px;
                                margin-top:8px;
                                flex-wrap:wrap;
                            ">

                                <div>
                                    <div style="
                                        font-size:24px;
                                        font-weight:800;
                                    ">
                                        {selected_format_html}
                                    </div>

                                    <div style="
                                        font-size:13px;
                                        opacity:0.7;
                                        margin-top:4px;
                                    ">
                                        {selected_name}
                                        • {selected_score:,} runs
                                    </div>
                                </div>

                                <div style="
                                    font-size:14px;
                                    font-weight:700;
                                ">
                                    {
                                        "👑 FORMAT CHAMPION"
                                        if selected_score == champion_score
                                        else "⚔️ RECORD CHALLENGER"
                                    }
                                </div>

                            </div>

                            <div style="
                                margin-top:14px;
                                height:8px;
                                border-radius:8px;
                                background:rgba(255,255,255,0.08);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:{selected_power:.1f}%;
                                    height:100%;
                                    border-radius:8px;
                                    background:
                                        linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                "></div>
                            </div>

                            <div style="
                                text-align:right;
                                font-size:10px;
                                opacity:0.55;
                                margin-top:4px;
                            ">
                                {selected_power:.1f}% of top record
                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Quick stats
                    # ------------------------------------------------

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "👑 Highest Score",
                            f"{champion_score:,}"
                        )

                    with col2:
                        st.metric(
                            "🎯 Selected Score",
                            f"{selected_score:,}"
                        )

                    with col3:
                        st.metric(
                            "🏏 Formats",
                            len(df)
                        )

                    with col4:
                        st.metric(
                            "📊 Avg Record",
                            f"{average_record:,.0f}"
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Record chart
                    # ------------------------------------------------

                    st.markdown("### 📊 Record-Breaking Scores")

                    chart_df = df[
                        ["format", "highest_score"]
                    ].set_index("format")

                    st.bar_chart(
                        chart_df,
                        y="highest_score",
                        use_container_width=True,
                        height=350
                    )

                    st.caption(
                        "Highest individual batting score recorded "
                        "for each format."
                    )

                    st.divider()

                    # ------------------------------------------------
                    # Record arena
                    # ------------------------------------------------

                    st.markdown("### ⚔️ Format Record Arena")

                    st.caption(
                        "Score Power is measured against the highest "
                        "score across the displayed formats."
                    )

                    max_score = max(
                        int(df["highest_score"].max()),
                        1
                    )

                    medals = ["🥇", "🥈", "🥉"]

                    for rank, (_, record) in enumerate(
                        df.iterrows(),
                        start=1
                    ):

                        fmt = html.escape(
                            str(record["format"])
                        )

                        player = html.escape(
                            str(record["player_name"])
                        )

                        score = int(
                            record["highest_score"]
                        )

                        power = min(
                            score / max_score * 100,
                            100
                        )

                        if rank <= 3:
                            rank_icon = medals[rank - 1]
                        else:
                            rank_icon = "⚡"

                        if rank == 1:
                            badge = "RECORD BOSS"
                        elif rank == 2:
                            badge = "ELITE RECORD"
                        elif rank == 3:
                            badge = "ELITE RECORD"
                        else:
                            badge = "RECORD HOLDER"

                        st.html(
                            f"""
                            <div style="
                                padding:16px 18px;
                                border:1px solid rgba(
                                    255,255,255,0.10
                                );
                                border-radius:14px;
                                margin:8px 0;
                                background:rgba(
                                    255,255,255,0.025
                                );
                            ">

                                <div style="
                                    display:flex;
                                    align-items:center;
                                    gap:14px;
                                    flex-wrap:wrap;
                                ">

                                    <div style="
                                        width:38px;
                                        text-align:center;
                                        font-size:22px;
                                    ">
                                        {rank_icon}
                                    </div>

                                    <div style="
                                        min-width:110px;
                                    ">

                                        <div style="
                                            font-size:15px;
                                            font-weight:700;
                                        ">
                                            {fmt}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            letter-spacing:1px;
                                            opacity:0.55;
                                            margin-top:3px;
                                        ">
                                            {badge}
                                        </div>

                                    </div>

                                    <div style="
                                        min-width:180px;
                                    ">

                                        <div style="
                                            font-size:14px;
                                            font-weight:650;
                                        ">
                                            {player}
                                        </div>

                                        <div style="
                                            font-size:11px;
                                            opacity:0.6;
                                            margin-top:3px;
                                        ">
                                            Highest individual score
                                        </div>

                                    </div>

                                    <div style="
                                        flex:1;
                                        min-width:150px;
                                    ">

                                        <div style="
                                            display:flex;
                                            justify-content:
                                                space-between;
                                            font-size:11px;
                                            margin-bottom:5px;
                                        ">
                                            <span>
                                                SCORE POWER
                                            </span>

                                            <span>
                                                {power:.1f}%
                                            </span>
                                        </div>

                                        <div style="
                                            height:8px;
                                            border-radius:8px;
                                            background:
                                                rgba(
                                                    255,255,255,0.08
                                                );
                                            overflow:hidden;
                                        ">

                                            <div style="
                                                width:{power:.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>

                                        </div>

                                    </div>

                                    <div style="
                                        min-width:95px;
                                        text-align:right;
                                    ">

                                        <div style="
                                            font-size:21px;
                                            font-weight:800;
                                        ">
                                            {score:,}
                                        </div>

                                        <div style="
                                            font-size:10px;
                                            opacity:0.55;
                                        ">
                                            RECORD
                                        </div>

                                    </div>

                                </div>

                            </div>
                            """
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Detailed standings
                    # ------------------------------------------------

                    st.markdown("### 📋 Batting Records")

                    table_df = df[
                        [
                            "format",
                            "player_name",
                            "highest_score",
                        ]
                    ].copy()

                    table_df.insert(
                        0,
                        "Rank",
                        range(1, len(table_df) + 1)
                    )

                    table_df["highest_score"] = (
                        table_df["highest_score"].astype(int)
                    )

                    table_df.columns = [
                        "Rank",
                        "Format",
                        "Player",
                        "Highest Score",
                    ]

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=260
                    )

                    st.download_button(
                        "Download results as CSV",
                        df.to_csv(index=False),
                        file_name="Q7.csv",
                        mime="text/csv"
                    )



            elif choice.startswith("Q8:"):

                st.subheader("🏆 2024 Cricket Series Universe")

                st.caption(
                    "Every series that began in 2024 • Explore the "
                    "calendar, formats, hosts, and planned match counts."
                )

                df = df.copy()

                # Normalize the Q8 result.
                df["series_name"] = (
                    df["series_name"]
                    .fillna("Unnamed Series")
                    .astype(str)
                    .str.strip()
                )

                df["host_country"] = (
                    df["host_country"]
                    .fillna("Unknown")
                    .astype(str)
                    .str.strip()
                )

                df["match_type"] = (
                    df["match_type"]
                    .fillna("Unknown")
                    .astype(str)
                    .str.strip()
                )

                df["start_date"] = pd.to_datetime(
                    df["start_date"],
                    errors="coerce"
                )

                df["total_matches"] = pd.to_numeric(
                    df["total_matches"],
                    errors="coerce"
                )

                df = df.dropna(
                    subset=["start_date"]
                ).copy()

                df = (
                    df.sort_values(
                        ["start_date", "series_name"],
                        ascending=[True, True],
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:

                    st.info(
                        "No cricket series starting in 2024 were found."
                    )

                else:

                    # ------------------------------------------------
                    # Important data-quality handling
                    # ------------------------------------------------

                    planned_available = int(
                        df["total_matches"].notna().sum()
                    )

                    planned_missing = int(
                        df["total_matches"].isna().sum()
                    )

                    # ------------------------------------------------
                    # Interactive filters
                    # ------------------------------------------------

                    st.markdown("### 🎯 Explore the 2024 Series")

                    match_types = sorted(
                        [
                            value
                            for value in df["match_type"].unique()
                            if value
                            and value.lower() != "unknown"
                        ]
                    )

                    filter_options = ["All"] + match_types

                    if "q8_selected_type" not in st.session_state:
                        st.session_state.q8_selected_type = "All"

                    if (
                        st.session_state.q8_selected_type
                        not in filter_options
                    ):
                        st.session_state.q8_selected_type = "All"

                    type_cols = st.columns(
                        min(len(filter_options), 4)
                    )

                    for index, match_type in enumerate(
                        filter_options
                    ):

                        with type_cols[
                            index % len(type_cols)
                        ]:

                            selected = (
                                match_type
                                == st.session_state.q8_selected_type
                            )

                            if st.button(
                                (
                                    f"👑 {match_type}"
                                    if selected
                                    else f"🏏 {match_type}"
                                ),
                                key=f"q8_type_{index}",
                                use_container_width=True
                            ):
                                st.session_state.q8_selected_type = match_type
                                st.rerun()

                    selected_type = (
                        st.session_state.q8_selected_type
                    )

                    if selected_type == "All":
                        display_df = df.copy()
                    else:
                        display_df = df[
                            df["match_type"].eq(selected_type)
                        ].copy()

                    if display_df.empty:

                        st.warning(
                            f"No series found for {selected_type}."
                        )

                    else:

                        # ------------------------------------------------
                        # Summary values
                        # ------------------------------------------------

                        series_count = len(display_df)

                        hosts = int(
                            display_df[
                                "host_country"
                            ]
                            .replace("Unknown", pd.NA)
                            .dropna()
                            .nunique()
                        )

                        known_planned = int(
                            display_df[
                                "total_matches"
                            ]
                            .fillna(0)
                            .sum()
                        )

                        available_planned = int(
                            display_df[
                                "total_matches"
                            ]
                            .notna()
                            .sum()
                        )

                        first_series = display_df.iloc[0]

                        # Largest planned series, when data exists.
                        planned_df = display_df.dropna(
                            subset=["total_matches"]
                        )

                        if not planned_df.empty:

                            planned_leader = (
                                planned_df
                                .sort_values(
                                    "total_matches",
                                    ascending=False,
                                    kind="stable"
                                )
                                .iloc[0]
                            )

                            planned_leader_name = html.escape(
                                str(
                                    planned_leader["series_name"]
                                )
                            )

                            planned_leader_matches = int(
                                planned_leader["total_matches"]
                            )

                        else:

                            planned_leader_name = "Not available"
                            planned_leader_matches = 0

                        # ------------------------------------------------
                        # Hero card
                        # ------------------------------------------------

                        hero_title = (
                            "THE 2024 SERIES CHAMPION"
                            if selected_type == "All"
                            else f"{html.escape(str(selected_type))} SERIES ARENA"
                        )

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:
                                    linear-gradient(
                                        135deg,
                                        rgba(255,215,0,0.18),
                                        rgba(255,255,255,0.035)
                                    );
                                box-shadow:
                                    0 8px 30px rgba(0,0,0,0.18);
                            ">

                                <div style="
                                    font-size:52px;
                                    line-height:1;
                                ">
                                    🏆
                                </div>

                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    {hero_title}
                                </div>

                                <div style="
                                    font-size:30px;
                                    font-weight:800;
                                    margin:9px 0;
                                ">
                                    {series_count:,} SERIES
                                </div>

                                <div style="
                                    font-size:14px;
                                    opacity:0.72;
                                ">
                                    {hosts:,} host countries
                                    • Started in calendar year 2024
                                </div>

                                <div style="
                                    margin:18px auto 0 auto;
                                    max-width:650px;
                                    height:10px;
                                    border-radius:10px;
                                    background:rgba(255,255,255,0.10);
                                    overflow:hidden;
                                ">
                                    <div style="
                                        width:100%;
                                        height:100%;
                                        border-radius:10px;
                                        background:
                                            linear-gradient(
                                                90deg,
                                                #ffd700,
                                                #ff9f1c
                                            );
                                    "></div>
                                </div>

                                <div style="
                                    font-size:11px;
                                    opacity:0.6;
                                    margin-top:7px;
                                ">
                                    🌍 2024 CRICKET CALENDAR POWER
                                </div>

                            </div>
                            """
                        )

                        # ------------------------------------------------
                        # Metrics
                        # ------------------------------------------------

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "🏏 Series",
                                f"{series_count:,}"
                            )

                        with col2:
                            st.metric(
                                "🌍 Host Countries",
                                hosts
                            )

                        with col3:
                            if available_planned:
                                st.metric(
                                    "🎟️ Planned Matches",
                                    f"{known_planned:,}"
                                )
                            else:
                                st.metric(
                                    "🎟️ Planned Matches",
                                    "N/A"
                                )

                        with col4:
                            st.metric(
                                "📅 First Start",
                                first_series[
                                    "start_date"
                                ].strftime("%d %b %Y")
                            )

                        # ------------------------------------------------
                        # Data quality notice
                        # ------------------------------------------------

                        if planned_missing > 0:

                            st.info(
                                f"ℹ️ Planned match count is available for "
                                f"{planned_available:,} of {len(df):,} series "
                                f"in the local dataset. The remaining "
                                f"{planned_missing:,} series are shown as "
                                f"**N/A** rather than being guessed."
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Chart 1 — series by match type
                        # ------------------------------------------------

                        st.markdown("### 📊 2024 Series Battle")

                        type_chart = (
                            display_df
                            .groupby("match_type")
                            .size()
                            .sort_values(ascending=False)
                            .rename("series_count")
                            .to_frame()
                        )

                        st.bar_chart(
                            type_chart,
                            y="series_count",
                            horizontal=True,
                            use_container_width=True,
                            height=320
                        )

                        # ------------------------------------------------
                        # Chart 2 — series starts by month
                        # ------------------------------------------------

                        st.markdown("### 📅 2024 Cricket Calendar")

                        month_chart_df = display_df.copy()

                        month_chart_df["month"] = (
                            month_chart_df["start_date"]
                            .dt.month
                        )

                        month_chart = (
                            month_chart_df
                            .groupby("month")
                            .size()
                            .reindex(
                                range(1, 13),
                                fill_value=0
                            )
                            .rename("series_started")
                            .to_frame()
                        )

                        month_chart.index = [
                            pd.Timestamp(
                                year=2024,
                                month=month,
                                day=1
                            ).strftime("%b")
                            for month in month_chart.index
                        ]

                        st.bar_chart(
                            month_chart,
                            y="series_started",
                            use_container_width=True,
                            height=300
                        )

                        # ------------------------------------------------
                        # Planned-match chart
                        # ------------------------------------------------

                        if available_planned:

                            st.markdown(
                                "### 🎟️ Planned Match Power"
                            )

                            planned_chart = (
                                display_df
                                .dropna(
                                    subset=["total_matches"]
                                )
                                .sort_values(
                                    "total_matches",
                                    ascending=False
                                )
                                .head(15)
                                [
                                    [
                                        "series_name",
                                        "total_matches"
                                    ]
                                ]
                                .set_index("series_name")
                            )

                            st.bar_chart(
                                planned_chart,
                                y="total_matches",
                                horizontal=True,
                                use_container_width=True,
                                height=420
                            )

                            st.caption(
                                "Top 15 series by planned match count "
                                "where the local database contains that value."
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Planned-match champion
                        # ------------------------------------------------

                        if available_planned:

                            st.html(
                                f"""
                                <div style="
                                    padding:20px 24px;
                                    border:1px solid
                                        rgba(255,255,255,0.12);
                                    border-radius:17px;
                                    margin-bottom:20px;
                                ">

                                    <div style="
                                        font-size:11px;
                                        letter-spacing:2px;
                                        opacity:0.6;
                                    ">
                                        🎟️ PLANNED MATCH CHAMPION
                                    </div>

                                    <div style="
                                        display:flex;
                                        justify-content:
                                            space-between;
                                        align-items:center;
                                        gap:20px;
                                        flex-wrap:wrap;
                                        margin-top:8px;
                                    ">

                                        <div>
                                            <div style="
                                                font-size:22px;
                                                font-weight:800;
                                            ">
                                                {planned_leader_name}
                                            </div>

                                            <div style="
                                                font-size:12px;
                                                opacity:0.65;
                                                margin-top:4px;
                                            ">
                                                Largest planned match slate
                                            </div>
                                        </div>

                                        <div style="
                                            text-align:right;
                                        ">

                                            <div style="
                                                font-size:26px;
                                                font-weight:800;
                                            ">
                                                {planned_leader_matches:,}
                                            </div>

                                            <div style="
                                                font-size:10px;
                                                opacity:0.55;
                                            ">
                                                MATCHES PLANNED
                                            </div>

                                        </div>

                                    </div>

                                </div>
                                """
                            )

                        # ------------------------------------------------
                        # Series timeline / cards
                        # ------------------------------------------------

                        st.markdown("### 🗺️ Series Timeline")

                        card_count = min(
                            len(display_df),
                            12
                        )

                        cards = display_df.head(
                            card_count
                        )

                        card_cols = st.columns(3)

                        for index, (_, series) in enumerate(
                            cards.iterrows()
                        ):

                            series_name = html.escape(
                                str(series["series_name"])
                            )

                            country = html.escape(
                                str(series["host_country"])
                            )

                            match_type = html.escape(
                                str(series["match_type"])
                            )

                            start_date = (
                                series["start_date"]
                                .strftime("%d %b %Y")
                            )

                            if pd.notna(
                                series["total_matches"]
                            ):

                                match_count = int(
                                    series["total_matches"]
                                )

                                matches_text = (
                                    f"{match_count:,} matches planned"
                                )

                            else:

                                matches_text = (
                                    "Planned matches: N/A"
                                )

                            with card_cols[
                                index % 3
                            ]:

                                st.html(
                                    f"""
                                    <div style="
                                        padding:20px;
                                        border:1px solid
                                            rgba(
                                                255,255,255,0.10
                                            );
                                        border-radius:17px;
                                        min-height:190px;
                                        margin-bottom:12px;
                                        background:
                                            rgba(
                                                255,255,255,0.025
                                            );
                                    ">

                                        <div style="
                                            font-size:10px;
                                            letter-spacing:1.5px;
                                            opacity:0.55;
                                        ">
                                            {match_type.upper()}
                                        </div>

                                        <div style="
                                            font-size:17px;
                                            font-weight:750;
                                            margin-top:7px;
                                            line-height:1.3;
                                        ">
                                            {series_name}
                                        </div>

                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                            margin-top:11px;
                                        ">
                                            🌍 {country}
                                        </div>

                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                            margin-top:5px;
                                        ">
                                            📅 {start_date}
                                        </div>

                                        <div style="
                                            font-size:12px;
                                            font-weight:700;
                                            margin-top:12px;
                                        ">
                                            🎟️ {matches_text}
                                        </div>

                                    </div>
                                    """
                                )

                        if len(display_df) > card_count:

                            st.caption(
                                f"Showing the first {card_count} series "
                                f"cards in chronological order. Use the "
                                f"format buttons above to explore the full dataset."
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Detailed standings
                        # ------------------------------------------------

                        st.markdown("### 📋 2024 Series Standings")

                        table_df = display_df[
                            [
                                "series_name",
                                "host_country",
                                "match_type",
                                "start_date",
                                "total_matches",
                            ]
                        ].copy()

                        table_df["start_date"] = (
                            table_df["start_date"]
                            .dt.strftime("%Y-%m-%d")
                        )

                        table_df["total_matches"] = (
                            table_df["total_matches"]
                            .apply(
                                lambda value:
                                int(value)
                                if pd.notna(value)
                                else "N/A"
                            )
                        )

                        table_df.columns = [
                            "Series",
                            "Host Country",
                            "Match Type",
                            "Start Date",
                            "Matches Planned",
                        ]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                            height=500
                        )

                        st.download_button(
                            "Download results as CSV",
                            display_df.to_csv(
                                index=False
                            ),
                            file_name="Q8.csv",
                            mime="text/csv"
                        )


            elif choice.startswith("Q9:"):
                st.subheader("🏆 All-Rounder Hall of Fame")
                st.caption(
                    "Players with more than 1,000 combined runs and more than 50 combined wickets "
                    "across Test, ODI, and T20 records in the local database."
                )

                df = df.copy()

                # Normalize the SQL result without changing the query data.
                df["player_name"] = (
                    df["player_name"]
                    .fillna("Unknown Player")
                    .astype(str)
                    .str.strip()
                )

                for column in ["total_runs", "total_wickets"]:
                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    ).fillna(0)

                df["total_runs"] = df["total_runs"].astype(int)
                df["total_wickets"] = df["total_wickets"].astype(int)

                df = (
                    df.sort_values(
                        ["total_runs", "total_wickets", "player_name"],
                        ascending=[False, False, True],
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:
                    st.info(
                        "No all-rounders currently meet the 1,000+ runs and 50+ wickets criteria."
                    )
                else:
                    # Keep the SQL ranking as the primary leaderboard order.
                    df["rank"] = range(1, len(df) + 1)

                    df["tier"] = "Elite"
                    df.loc[
                        (df["total_runs"] < 3000) | (df["total_wickets"] < 100),
                        "tier"
                    ] = "Rising Star"
                    df.loc[
                        (df["total_runs"] >= 5000) & (df["total_wickets"] >= 200),
                        "tier"
                    ] = "Legend"

                    df["run_progress"] = (
                        df["total_runs"] / 10000
                    ).clip(upper=1)
                    df["wicket_progress"] = (
                        df["total_wickets"] / 500
                    ).clip(upper=1)

                    leader = df.iloc[0]
                    leader_name = html.escape(str(leader["player_name"]))
                    leader_runs = int(leader["total_runs"])
                    leader_wickets = int(leader["total_wickets"])

                    total_players = len(df)
                    combined_runs = int(df["total_runs"].sum())
                    combined_wickets = int(df["total_wickets"].sum())

                    # ------------------------------------------------
                    # Champion hero
                    # ------------------------------------------------
                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:linear-gradient(
                                135deg,
                                rgba(255,215,0,0.18),
                                rgba(255,255,255,0.035)
                            );
                            box-shadow:0 8px 30px rgba(0,0,0,0.18);
                        ">
                            <div style="font-size:52px;line-height:1;">🏆</div>
                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                ALL-ROUNDER CHAMPION
                            </div>
                            <div style="
                                font-size:30px;
                                font-weight:800;
                                margin:9px 0;
                            ">
                                {leader_name}
                            </div>
                            <div style="font-size:15px;opacity:0.75;">
                                {leader_runs:,} runs • {leader_wickets:,} wickets • {leader['tier']}
                            </div>
                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:linear-gradient(90deg,#ffd700,#ff9f1c);
                                "></div>
                            </div>
                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                🏏 BAT + ⚾ BALL = COMPLETE PLAYER
                            </div>
                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Scoreboard
                    # ------------------------------------------------
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("👑 Champion", leader_name)

                    with col2:
                        st.metric("🏏 Combined Runs", f"{combined_runs:,}")

                    with col3:
                        st.metric("⚾ Combined Wickets", f"{combined_wickets:,}")

                    with col4:
                        st.metric("🎖️ Qualifying Players", total_players)

                    st.divider()

                    # ------------------------------------------------
                    # Interactive filters
                    # ------------------------------------------------
                    st.markdown("### 🎯 All-Rounder Challenge")

                    filter_col1, filter_col2, filter_col3 = st.columns(3)

                    with filter_col1:
                        tier_options = ["All"] + sorted(df["tier"].unique().tolist())
                        selected_tier = st.selectbox(
                            "Filter by tier",
                            tier_options,
                            key="q9_tier_filter"
                        )

                    with filter_col2:
                        max_rank = max(len(df), 1)
                        selected_rank = st.slider(
                            "Show players through rank",
                            min_value=1,
                            max_value=max_rank,
                            value=max_rank,
                            key="q9_rank_filter"
                        )

                    with filter_col3:
                        player_options = ["All players"] + df["player_name"].tolist()
                        selected_player = st.selectbox(
                            "Inspect a player",
                            player_options,
                            key="q9_player_filter"
                        )

                    display_df = df[df["rank"] <= selected_rank].copy()

                    if selected_tier != "All":
                        display_df = display_df[
                            display_df["tier"] == selected_tier
                        ].copy()

                    if display_df.empty:
                        st.warning("No players match the selected filters.")
                    else:
                        # ------------------------------------------------
                        # Player inspection
                        # ------------------------------------------------
                        if selected_player != "All players":
                            selected_row = df[
                                df["player_name"] == selected_player
                            ].iloc[0]

                            st.markdown("### 🔎 Player Spotlight")

                            spot1, spot2, spot3, spot4 = st.columns(4)

                            with spot1:
                                st.metric(
                                    "Rank",
                                    f"#{int(selected_row['rank'])}"
                                )

                            with spot2:
                                st.metric(
                                    "🏏 Runs",
                                    f"{int(selected_row['total_runs']):,}"
                                )

                            with spot3:
                                st.metric(
                                    "⚾ Wickets",
                                    f"{int(selected_row['total_wickets']):,}"
                                )

                            with spot4:
                                st.metric(
                                    "🎖️ Tier",
                                    str(selected_row["tier"])
                                )

                            run_pct = float(selected_row["run_progress"])
                            wicket_pct = float(selected_row["wicket_progress"])

                            progress1, progress2 = st.columns(2)

                            with progress1:
                                st.caption("🏏 Run Power — progress to 10,000")
                                st.progress(run_pct)

                            with progress2:
                                st.caption("⚾ Wicket Power — progress to 500")
                                st.progress(wicket_pct)

                            st.divider()

                        # ------------------------------------------------
                        # Top 3 podium
                        # ------------------------------------------------
                        st.markdown("### 🥇 All-Rounder Podium")

                        podium = display_df.head(3)
                        podium_cols = st.columns(len(podium))
                        medals = ["🥇", "🥈", "🥉"]

                        for col, (_, player), medal in zip(
                            podium_cols,
                            podium.iterrows(),
                            medals
                        ):
                            player_name = html.escape(str(player["player_name"]))
                            runs = int(player["total_runs"])
                            wickets = int(player["total_wickets"])
                            rank = int(player["rank"])

                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:22px;
                                        border:1px solid rgba(255,255,255,0.12);
                                        border-radius:17px;
                                        text-align:center;
                                        min-height:190px;
                                        background:rgba(255,255,255,0.025);
                                    ">
                                        <div style="font-size:38px;">{medal}</div>
                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:0.6;
                                        ">RANK #{rank}</div>
                                        <div style="
                                            font-size:20px;
                                            font-weight:800;
                                            margin:8px 0;
                                        ">{player_name}</div>
                                        <div style="font-size:13px;opacity:0.75;">
                                            🏏 {runs:,} runs<br>
                                            ⚾ {wickets:,} wickets
                                        </div>
                                        <div style="
                                            margin-top:12px;
                                            font-size:11px;
                                            font-weight:700;
                                        ">{player['tier']}</div>
                                    </div>
                                    """
                                )

                        st.divider()

                        # ------------------------------------------------
                        # Interactive charts
                        # ------------------------------------------------
                        st.markdown("### 📊 Runs vs Wickets Battle")
                        st.caption(
                            "Each point represents one qualifying all-rounder. "
                            "Move across the chart to compare batting and bowling output."
                        )

                        chart_df = display_df[
                            ["player_name", "total_runs", "total_wickets"]
                        ].copy()

                        st.scatter_chart(
                            chart_df,
                            x="total_runs",
                            y="total_wickets",
                            x_label="Total Runs",
                            y_label="Total Wickets",
                            use_container_width=True,
                            height=450
                        )

                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            st.markdown("### 🏏 Top Run Scorers")
                            runs_chart = (
                                display_df
                                .sort_values(
                                    "total_runs",
                                    ascending=False
                                )
                                .head(10)
                                [["player_name", "total_runs"]]
                                .set_index("player_name")
                            )
                            st.bar_chart(
                                runs_chart,
                                y="total_runs",
                                horizontal=True,
                                use_container_width=True,
                                height=420
                            )

                        with chart_col2:
                            st.markdown("### ⚾ Top Wicket Takers")
                            wickets_chart = (
                                display_df
                                .sort_values(
                                    "total_wickets",
                                    ascending=False
                                )
                                .head(10)
                                [["player_name", "total_wickets"]]
                                .set_index("player_name")
                            )
                            st.bar_chart(
                                wickets_chart,
                                y="total_wickets",
                                horizontal=True,
                                use_container_width=True,
                                height=420
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Achievement cards
                        # ------------------------------------------------
                        st.markdown("### 🎮 Achievement Board")

                        achievement_cols = st.columns(4)
                        achievements = [
                            (
                                "🔥 5K Club",
                                int((df["total_runs"] >= 5000).sum()),
                                "players with 5,000+ runs"
                            ),
                            (
                                "⚡ 200 Wicket Club",
                                int((df["total_wickets"] >= 200).sum()),
                                "players with 200+ wickets"
                            ),
                            (
                                "💎 Double Threat",
                                int(
                                    (
                                        (df["total_runs"] >= 5000)
                                        & (df["total_wickets"] >= 200)
                                    ).sum()
                                ),
                                "5K runs + 200 wickets"
                            ),
                            (
                                "👑 Elite Squad",
                                int((df["tier"] == "Legend").sum()),
                                "Legend-tier all-rounders"
                            )
                        ]

                        for col, (title, count, description) in zip(
                            achievement_cols,
                            achievements
                        ):
                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:18px;
                                        border:1px solid rgba(255,255,255,0.10);
                                        border-radius:15px;
                                        min-height:145px;
                                        text-align:center;
                                    ">
                                        <div style="font-size:17px;font-weight:800;">
                                            {title}
                                        </div>
                                        <div style="
                                            font-size:30px;
                                            font-weight:800;
                                            margin:8px 0;
                                        ">
                                            {count}
                                        </div>
                                        <div style="font-size:11px;opacity:0.65;">
                                            {description}
                                        </div>
                                    </div>
                                    """
                                )

                        st.divider()

                        # ------------------------------------------------
                        # Detailed leaderboard
                        # ------------------------------------------------
                        st.markdown("### 📋 All-Rounder Leaderboard")

                        table_df = display_df[
                            [
                                "rank",
                                "player_name",
                                "total_runs",
                                "total_wickets",
                                "format",
                                "tier"
                            ]
                        ].copy()

                        table_df.columns = [
                            "Rank",
                            "Player",
                            "Total Runs",
                            "Total Wickets",
                            "Formats",
                            "Tier"
                        ]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                            height=520,
                            column_config={
                                "Rank": st.column_config.NumberColumn(
                                    "Rank",
                                    format="%d"
                                ),
                                "Total Runs": st.column_config.NumberColumn(
                                    "Total Runs",
                                    format="%d"
                                ),
                                "Total Wickets": st.column_config.NumberColumn(
                                    "Total Wickets",
                                    format="%d"
                                )
                            }
                        )

                        st.download_button(
                            "Download Q9 results as CSV",
                            display_df.to_csv(index=False),
                            file_name="Q9_all_rounder_hall_of_fame.csv",
                            mime="text/csv"
                        )

            elif choice.startswith("Q10:"):
                st.subheader("⚔️ Last 20 Match Battle")
                st.caption(
                    "The 20 matches returned by Q10 • Most recent first • "
                    "Explore winners, margins, formats, venues, and match details."
                )

                df = df.copy()

                # Normalize the SQL result without changing the underlying rows.
                df["match_description"] = (
                    df["match_description"]
                    .fillna("Match description unavailable")
                    .astype(str)
                    .str.strip()
                )

                for column in ["team_1", "team_2", "winning_team", "venue_name"]:
                    df[column] = (
                        df[column]
                        .fillna("Not available")
                        .astype(str)
                        .str.strip()
                    )

                df["victory_type"] = (
                    df["victory_type"]
                    .fillna("Not recorded")
                    .astype(str)
                    .str.strip()
                )

                df["victory_margin"] = pd.to_numeric(
                    df["victory_margin"],
                    errors="coerce"
                )

                df["match_date"] = pd.to_datetime(
                    df["match_date"],
                    errors="coerce"
                )

                df["status"] = (
                    df["status"]
                    .fillna("Result status unavailable")
                    .astype(str)
                    .str.strip()
                )

                # Keep the SQL order as the official Q10 ranking.
                df = df.reset_index(drop=True)
                df["rank"] = range(1, len(df) + 1)

                df["victory_type_normalized"] = (
                    df["victory_type"]
                    .str.lower()
                    .str.strip()
                )

                def q10_margin_text(row):
                    if pd.isna(row["victory_margin"]):
                        return "Margin not recorded"
                    margin = int(row["victory_margin"])
                    victory_type = row["victory_type_normalized"]
                    if victory_type == "runs":
                        return f"{margin:,} runs"
                    if victory_type == "wickets":
                        return f"{margin:,} wickets"
                    return f"{margin:,} {row['victory_type']}"

                df["margin_text"] = df.apply(q10_margin_text, axis=1)

                if df.empty:
                    st.info("Q10 returned no completed matches.")
                else:
                    # ------------------------------------------------
                    # Match statistics
                    # ------------------------------------------------
                    total_matches = len(df)
                    run_wins = int(
                        (df["victory_type_normalized"] == "runs").sum()
                    )
                    wicket_wins = int(
                        (df["victory_type_normalized"] == "wickets").sum()
                    )
                    margin_recorded = int(
                        df["victory_margin"].notna().sum()
                    )
                    venues = int(df["venue_name"].nunique())

                    # Winner with the most appearances in the 20-match window.
                    winner_counts = (
                        df["winning_team"]
                        .loc[
                            ~df["winning_team"].isin(
                                ["", "Not available", "None", "nan"]
                            )
                        ]
                        .value_counts()
                    )

                    top_winner = (
                        str(winner_counts.index[0])
                        if not winner_counts.empty
                        else "Not available"
                    )
                    top_winner_count = (
                        int(winner_counts.iloc[0])
                        if not winner_counts.empty
                        else 0
                    )

                    # ------------------------------------------------
                    # Champion hero
                    # ------------------------------------------------
                    latest = df.iloc[0]
                    latest_description = html.escape(
                        str(latest["match_description"])
                    )
                    latest_winner = html.escape(
                        str(latest["winning_team"])
                    )
                    latest_margin = html.escape(
                        str(latest["margin_text"])
                    )

                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:linear-gradient(
                                135deg,
                                rgba(255,215,0,0.18),
                                rgba(255,255,255,0.035)
                            );
                            box-shadow:0 8px 30px rgba(0,0,0,0.18);
                        ">
                            <div style="font-size:52px;line-height:1;">🏆</div>
                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                MOST RECENT MATCH
                            </div>
                            <div style="
                                font-size:25px;
                                font-weight:800;
                                margin:9px 0;
                            ">
                                {latest_description}
                            </div>
                            <div style="font-size:15px;opacity:0.75;">
                                🏆 {latest_winner} • {latest_margin}
                            </div>
                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:linear-gradient(90deg,#ffd700,#ff9f1c);
                                "></div>
                            </div>
                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                ⚔️ 20-MATCH RECENT FORM ARENA
                            </div>
                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Scoreboard
                    # ------------------------------------------------
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("🏏 Matches", total_matches)

                    with col2:
                        st.metric("🏃 Run Wins", run_wins)

                    with col3:
                        st.metric("⚡ Wicket Wins", wicket_wins)

                    with col4:
                        st.metric("🏟️ Venues", venues)

                    st.divider()

                    # ------------------------------------------------
                    # Working filter buttons
                    # ------------------------------------------------
                    st.markdown("### 🎯 Match Battle Controls")

                    if "q10_view" not in st.session_state:
                        st.session_state.q10_view = "All"

                    button_options = [
                        ("All", "🏏 All Matches"),
                        ("runs", "🏃 Wins by Runs"),
                        ("wickets", "⚡ Wins by Wickets"),
                        ("other", "⏳ Other / Unrecorded")
                    ]

                    button_cols = st.columns(len(button_options))

                    for col, (value, label) in zip(
                        button_cols,
                        button_options
                    ):
                        with col:
                            selected = (
                                st.session_state.q10_view == value
                            )
                            if st.button(
                                (
                                    f"👑 {label}"
                                    if selected
                                    else label
                                ),
                                key=f"q10_view_{value}",
                                use_container_width=True
                            ):
                                st.session_state.q10_view = value
                                st.rerun()

                    selected_view = st.session_state.q10_view

                    if selected_view == "All":
                        display_df = df.copy()
                    elif selected_view in ["runs", "wickets"]:
                        display_df = df[
                            df["victory_type_normalized"] == selected_view
                        ].copy()
                    else:
                        display_df = df[
                            ~df["victory_type_normalized"].isin(
                                ["runs", "wickets"]
                            )
                        ].copy()

                    # ------------------------------------------------
                    # Secondary filters
                    # ------------------------------------------------
                    filter_col1, filter_col2 = st.columns(2)

                    with filter_col1:
                        venue_options = [
                            "All venues"
                        ] + sorted(df["venue_name"].unique().tolist())
                        selected_venue = st.selectbox(
                            "Filter by venue",
                            venue_options,
                            key="q10_venue_filter"
                        )

                    with filter_col2:
                        rank_limit = st.slider(
                            "Show through recent rank",
                            min_value=1,
                            max_value=max(total_matches, 1),
                            value=total_matches,
                            key="q10_rank_filter"
                        )

                    display_df = display_df[
                        display_df["rank"] <= rank_limit
                    ].copy()

                    if selected_venue != "All venues":
                        display_df = display_df[
                            display_df["venue_name"] == selected_venue
                        ].copy()

                    st.caption(
                        f"Showing {len(display_df)} of {total_matches} Q10 matches"
                    )

                    if display_df.empty:
                        st.warning("No matches match the selected filters.")
                    else:
                        # ------------------------------------------------
                        # Match spotlight
                        # ------------------------------------------------
                        st.markdown("### 🔎 Match Spotlight")

                        spotlight_options = [
                            f"#{int(row['rank'])} — {row['match_description']}"
                            for _, row in display_df.iterrows()
                        ]

                        selected_spotlight = st.selectbox(
                            "Inspect a match",
                            spotlight_options,
                            key="q10_match_spotlight"
                        )

                        spotlight_index = spotlight_options.index(
                            selected_spotlight
                        )
                        spotlight = display_df.iloc[spotlight_index]

                        spot1, spot2, spot3, spot4 = st.columns(4)

                        with spot1:
                            st.metric(
                                "Recent Rank",
                                f"#{int(spotlight['rank'])}"
                            )

                        with spot2:
                            st.metric(
                                "🏆 Winner",
                                str(spotlight["winning_team"])
                            )

                        with spot3:
                            st.metric(
                                "📏 Margin",
                                str(spotlight["margin_text"])
                            )

                        with spot4:
                            st.metric(
                                "🏟️ Venue",
                                str(spotlight["venue_name"])
                            )

                        st.html(
                            f"""
                            <div style="
                                padding:18px;
                                border:1px solid rgba(255,255,255,0.10);
                                border-radius:15px;
                                margin:14px 0 20px 0;
                                background:rgba(255,255,255,0.025);
                            ">
                                <div style="
                                    font-size:11px;
                                    letter-spacing:2px;
                                    opacity:0.6;
                                ">
                                    MATCH DETAIL
                                </div>
                                <div style="
                                    font-size:20px;
                                    font-weight:800;
                                    margin:8px 0;
                                ">
                                    {html.escape(str(spotlight['team_1']))}
                                    <span style="opacity:0.45;"> VS </span>
                                    {html.escape(str(spotlight['team_2']))}
                                </div>
                                <div style="font-size:13px;opacity:0.72;">
                                    📅 {
                                        spotlight['match_date'].strftime('%d %b %Y')
                                        if pd.notna(spotlight['match_date'])
                                        else 'Date unavailable'
                                    }
                                    &nbsp; • &nbsp;
                                    🏟️ {html.escape(str(spotlight['venue_name']))}
                                </div>
                                <div style="font-size:13px;opacity:0.72;margin-top:7px;">
                                    🏆 Winner: {html.escape(str(spotlight['winning_team']))}
                                    &nbsp; • &nbsp;
                                    📏 {html.escape(str(spotlight['margin_text']))}
                                </div>
                                <div style="font-size:12px;opacity:0.58;margin-top:7px;">
                                    📌 {html.escape(str(spotlight['status']))}
                                </div>
                            </div>
                            """
                        )

                        st.divider()

                        # ------------------------------------------------
                        # Rankings
                        # ------------------------------------------------
                        st.markdown("### 🏆 Recent Match Rankings")

                        ranking_df = display_df.copy()
                        ranking_df["margin_rank"] = ranking_df[
                            "victory_margin"
                        ].rank(
                            method="first",
                            ascending=False,
                            na_option="bottom"
                        )

                        ranking_df = ranking_df.sort_values(
                            ["victory_margin", "rank"],
                            ascending=[False, True],
                            na_position="last",
                            kind="stable"
                        ).reset_index(drop=True)

                        max_margin = max(
                            float(
                                ranking_df["victory_margin"].max()
                            )
                            if ranking_df["victory_margin"].notna().any()
                            else 1,
                            1
                        )

                        for position, (_, match) in enumerate(
                            ranking_df.iterrows(),
                            start=1
                        ):
                            margin = match["victory_margin"]
                            power = (
                                min(
                                    float(margin) / max_margin * 100,
                                    100
                                )
                                if pd.notna(margin)
                                else 0
                            )

                            if position == 1:
                                rank_icon = "👑"
                                badge = "MARGIN KING"
                            elif position == 2:
                                rank_icon = "🥈"
                                badge = "ELITE"
                            elif position == 3:
                                rank_icon = "🥉"
                                badge = "ELITE"
                            elif position <= 5:
                                rank_icon = "🔥"
                                badge = "TOP 5"
                            else:
                                rank_icon = "⚡"
                                badge = "MATCH RANK"

                            winner = html.escape(
                                str(match["winning_team"])
                            )
                            description = html.escape(
                                str(match["match_description"])
                            )
                            margin_text = html.escape(
                                str(match["margin_text"])
                            )

                            st.html(
                                f"""
                                <div style="
                                    padding:15px 18px;
                                    border:1px solid rgba(255,255,255,0.10);
                                    border-radius:14px;
                                    margin:8px 0;
                                    background:rgba(255,255,255,0.025);
                                ">
                                    <div style="
                                        display:flex;
                                        align-items:center;
                                        gap:14px;
                                    ">
                                        <div style="
                                            width:38px;
                                            text-align:center;
                                            font-size:22px;
                                        ">
                                            {rank_icon}
                                        </div>
                                        <div style="min-width:190px;">
                                            <div style="
                                                font-size:15px;
                                                font-weight:700;
                                            ">
                                                #{position} {winner}
                                            </div>
                                            <div style="
                                                font-size:10px;
                                                letter-spacing:1px;
                                                opacity:0.55;
                                                margin-top:3px;
                                            ">
                                                {badge}
                                            </div>
                                        </div>
                                        <div style="flex:1;min-width:120px;">
                                            <div style="
                                                display:flex;
                                                justify-content:space-between;
                                                font-size:11px;
                                                margin-bottom:5px;
                                            ">
                                                <span>VICTORY POWER</span>
                                                <span>{power:.1f}%</span>
                                            </div>
                                            <div style="
                                                height:8px;
                                                border-radius:8px;
                                                background:rgba(255,255,255,0.08);
                                                overflow:hidden;
                                            ">
                                                <div style="
                                                    width:{power:.1f}%;
                                                    height:100%;
                                                    border-radius:8px;
                                                    background:linear-gradient(
                                                        90deg,#ffd700,#ff9f1c
                                                    );
                                                "></div>
                                            </div>
                                        </div>
                                        <div style="
                                            min-width:120px;
                                            text-align:right;
                                        ">
                                            <div style="
                                                font-size:17px;
                                                font-weight:800;
                                            ">
                                                {margin_text}
                                            </div>
                                            <div style="
                                                font-size:10px;
                                                opacity:0.55;
                                                margin-top:3px;
                                            ">
                                                {description[:55]}
                                                {'...' if len(description) > 55 else ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                """
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Interactive charts
                        # ------------------------------------------------
                        st.markdown("### 📊 Match Analytics")
                        st.caption(
                            "Use the controls above to change the chart population. "
                            "The charts update from the filtered Q10 result."
                        )

                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            st.markdown("#### 📏 Victory Margin Battle")

                            margin_chart = display_df[
                                display_df["victory_margin"].notna()
                            ][
                                [
                                    "winning_team",
                                    "victory_margin",
                                    "victory_type"
                                ]
                            ].copy()

                            margin_chart["label"] = (
                                margin_chart["winning_team"].astype(str)
                                + " — "
                                + margin_chart["victory_margin"].astype(int).astype(str)
                                + " "
                                + margin_chart["victory_type"].astype(str)
                            )

                            margin_chart = (
                                margin_chart
                                .sort_values(
                                    "victory_margin",
                                    ascending=False
                                )
                                .head(10)
                                .set_index("label")
                            )

                            if margin_chart.empty:
                                st.info("No numeric victory margins are available for this view.")
                            else:
                                st.bar_chart(
                                    margin_chart,
                                    y="victory_margin",
                                    horizontal=True,
                                    use_container_width=True,
                                    height=400
                                )

                        with chart_col2:
                            st.markdown("#### ⚔️ Victory Type Split")

                            type_chart = (
                                display_df["victory_type"]
                                .replace(
                                    {
                                        "": "Not recorded",
                                        "nan": "Not recorded",
                                        "None": "Not recorded"
                                    }
                                )
                                .value_counts()
                                .rename("matches")
                                .to_frame()
                            )

                            st.bar_chart(
                                type_chart,
                                y="matches",
                                use_container_width=True,
                                height=400
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Venue battle
                        # ------------------------------------------------
                        st.markdown("### 🏟️ Venue Battle")

                        venue_chart = (
                            display_df
                            .groupby("venue_name")
                            .size()
                            .sort_values(ascending=False)
                            .head(10)
                            .rename("matches")
                            .to_frame()
                        )

                        st.bar_chart(
                            venue_chart,
                            y="matches",
                            horizontal=True,
                            use_container_width=True,
                            height=400
                        )

                        st.divider()

                        # ------------------------------------------------
                        # Achievement board
                        # ------------------------------------------------
                        st.markdown("### 🎮 Match Achievements")

                        largest_run_margin = display_df.loc[
                            display_df["victory_type_normalized"] == "runs",
                            "victory_margin"
                        ].max()

                        largest_wicket_margin = display_df.loc[
                            display_df["victory_type_normalized"] == "wickets",
                            "victory_margin"
                        ].max()

                        achievement_cols = st.columns(4)
                        achievements = [
                            (
                                "🔥 Run Domination",
                                f"{int(largest_run_margin):,} runs"
                                if pd.notna(largest_run_margin)
                                else "N/A",
                                "largest recorded run margin"
                            ),
                            (
                                "⚡ Wicket Domination",
                                f"{int(largest_wicket_margin):,} wickets"
                                if pd.notna(largest_wicket_margin)
                                else "N/A",
                                "largest recorded wicket margin"
                            ),
                            (
                                "👑 Most Wins",
                                top_winner,
                                f"{top_winner_count} appearances in Q10"
                            ),
                            (
                                "🏟️ Venue Explorer",
                                f"{venues}",
                                "unique venues in the 20-match set"
                            )
                        ]

                        for col, (title, value, description) in zip(
                            achievement_cols,
                            achievements
                        ):
                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:18px;
                                        border:1px solid rgba(255,255,255,0.10);
                                        border-radius:15px;
                                        min-height:150px;
                                        text-align:center;
                                    ">
                                        <div style="
                                            font-size:17px;
                                            font-weight:800;
                                        ">
                                            {html.escape(str(title))}
                                        </div>
                                        <div style="
                                            font-size:21px;
                                            font-weight:800;
                                            margin:8px 0;
                                        ">
                                            {html.escape(str(value))}
                                        </div>
                                        <div style="
                                            font-size:11px;
                                            opacity:0.65;
                                        ">
                                            {html.escape(str(description))}
                                        </div>
                                    </div>
                                    """
                                )

                        st.divider()

                        # ------------------------------------------------
                        # Detailed leaderboard
                        # ------------------------------------------------
                        st.markdown("### 📋 Complete Q10 Leaderboard")

                        table_df = display_df[
                            [
                                "rank",
                                "match_description",
                                "team_1",
                                "team_2",
                                "winning_team",
                                "victory_margin",
                                "victory_type",
                                "venue_name",
                                "match_date",
                                "status"
                            ]
                        ].copy()

                        table_df["victory_margin"] = table_df.apply(
                            lambda row: (
                                f"{int(row['victory_margin']):,}"
                                if pd.notna(row["victory_margin"])
                                else "N/A"
                            ),
                            axis=1
                        )

                        table_df["match_date"] = table_df[
                            "match_date"
                        ].apply(
                            lambda value: (
                                value.strftime("%Y-%m-%d")
                                if pd.notna(value)
                                else "N/A"
                            )
                        )

                        table_df.columns = [
                            "Rank",
                            "Match Description",
                            "Team 1",
                            "Team 2",
                            "Winning Team",
                            "Victory Margin",
                            "Victory Type",
                            "Venue",
                            "Match Date",
                            "Status"
                        ]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                            height=560
                        )

                        st.download_button(
                            "Download Q10 results as CSV",
                            display_df.to_csv(index=False),
                            file_name="Q10_last_20_matches.csv",
                            mime="text/csv"
                        )

            elif choice.startswith("Q11:"):

                # ------------------------------------------------
                # Q11: Format Masters
                # ------------------------------------------------
                # Only players with positive runs in all three
                # requested formats are included.
                # T20I and IT20 are treated as the same T20I bucket.
                # The database remains the source of truth.

                df = df.copy()

                numeric_columns = [
                    "test_runs",
                    "odi_runs",
                    "t20i_runs",
                    "overall_avg"
                ]

                for column in numeric_columns:
                    if column in df.columns:
                        df[column] = pd.to_numeric(
                            df[column],
                            errors="coerce"
                        )

                required_columns = [
                    "player_name",
                    "test_runs",
                    "odi_runs",
                    "t20i_runs",
                    "overall_avg"
                ]

                missing_columns = [
                    column
                    for column in required_columns
                    if column not in df.columns
                ]

                if missing_columns:
                    st.error(
                        "Q11 is missing required columns: "
                        + ", ".join(missing_columns)
                    )

                else:
                    # Defensive filtering in the UI as well as in SQL.
                    # This guarantees that zero-run players cannot enter
                    # the leaderboard if the query definition changes.
                    df = df[
                        (df["test_runs"] > 0)
                        & (df["odi_runs"] > 0)
                        & (df["t20i_runs"] > 0)
                    ].copy()

                    df["total_runs"] = (
                        df["test_runs"]
                        + df["odi_runs"]
                        + df["t20i_runs"]
                    )

                    df["format_count"] = 3

                    df["test_share"] = (
                        df["test_runs"]
                        / df["total_runs"]
                        * 100
                    )
                    df["odi_share"] = (
                        df["odi_runs"]
                        / df["total_runs"]
                        * 100
                    )
                    df["t20i_share"] = (
                        df["t20i_runs"]
                        / df["total_runs"]
                        * 100
                    )

                    df["format_spread"] = (
                        df[
                            [
                                "test_share",
                                "odi_share",
                                "t20i_share"
                            ]
                        ].max(axis=1)
                        - df[
                            [
                                "test_share",
                                "odi_share",
                                "t20i_share"
                            ]
                        ].min(axis=1)
                    )

                    df = (
                        df.sort_values(
                            "total_runs",
                            ascending=False,
                            kind="stable"
                        )
                        .reset_index(drop=True)
                    )

                    if df.empty:
                        st.info(
                            "No players have recorded runs in Test, ODI, "
                            "and T20I/IT20 in the current database."
                        )

                    else:
                        # ------------------------------------------------
                        # Hall of Fame hero
                        # ------------------------------------------------
                        leader = df.iloc[0]
                        leader_name = html.escape(
                            str(leader["player_name"])
                        )
                        leader_total = int(leader["total_runs"])
                        leader_avg = float(leader["overall_avg"])

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                                box-shadow:0 8px 30px rgba(0,0,0,0.18);
                            ">
                                <div style="font-size:52px;line-height:1;">
                                    👑
                                </div>
                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    FORMAT MASTER
                                </div>
                                <div style="
                                    font-size:32px;
                                    font-weight:800;
                                    margin:8px 0;
                                ">
                                    {leader_name}
                                </div>
                                <div style="font-size:25px;font-weight:800;">
                                    {leader_total:,} COMBINED RUNS
                                </div>
                                <div style="
                                    margin-top:8px;
                                    opacity:0.75;
                                    font-size:14px;
                                ">
                                    {leader_avg:.2f} overall batting average
                                    &nbsp; • &nbsp;
                                    runs recorded in all 3 formats
                                </div>
                                <div style="
                                    margin:18px auto 0 auto;
                                    max-width:650px;
                                    height:10px;
                                    border-radius:10px;
                                    background:rgba(255,255,255,0.10);
                                    overflow:hidden;
                                ">
                                    <div style="
                                        width:100%;
                                        height:100%;
                                        border-radius:10px;
                                        background:linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                    "></div>
                                </div>
                                <div style="
                                    font-size:11px;
                                    opacity:0.6;
                                    margin-top:7px;
                                ">
                                    🏆 THREE-FORMAT CLUB
                                </div>
                            </div>
                            """
                        )

                        # ------------------------------------------------
                        # Quick stats
                        # ------------------------------------------------
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "🏏 3-Format Players",
                                len(df)
                            )

                        with col2:
                            st.metric(
                                "🔥 Top Combined Runs",
                                f"{leader_total:,}"
                            )

                        with col3:
                            st.metric(
                                "📈 Best Overall Avg",
                                f"{df['overall_avg'].max():.2f}"
                            )

                        with col4:
                            st.metric(
                                "📊 Median Combined Runs",
                                f"{df['total_runs'].median():,.0f}"
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Interactive view buttons
                        # ------------------------------------------------
                        st.markdown("### 🎮 Choose Your Battle Mode")

                        if "q11_view" not in st.session_state:
                            st.session_state["q11_view"] = "Combined Runs"

                        button_cols = st.columns(4)

                        with button_cols[0]:
                            if st.button(
                                "🏆 Combined Runs",
                                key="q11_btn_total",
                                width="stretch"
                            ):
                                st.session_state["q11_view"] = "Combined Runs"

                        with button_cols[1]:
                            if st.button(
                                "📈 Best Average",
                                key="q11_btn_average",
                                width="stretch"
                            ):
                                st.session_state["q11_view"] = "Best Average"

                        with button_cols[2]:
                            if st.button(
                                "⚖️ Most Balanced",
                                key="q11_btn_balance",
                                width="stretch"
                            ):
                                st.session_state["q11_view"] = "Most Balanced"

                        with button_cols[3]:
                            if st.button(
                                "🔥 Format Power",
                                key="q11_btn_format",
                                width="stretch"
                            ):
                                st.session_state["q11_view"] = "Format Power"

                        current_view = st.session_state["q11_view"]

                        # ------------------------------------------------
                        # Rankings controlled by buttons
                        # ------------------------------------------------
                        if current_view == "Best Average":
                            ranking_df = (
                                df.sort_values(
                                    ["overall_avg", "total_runs"],
                                    ascending=[False, False],
                                    kind="stable"
                                )
                                .reset_index(drop=True)
                            )
                            ranking_metric = "overall_avg"
                            ranking_label = "Overall Average"

                        elif current_view == "Most Balanced":
                            ranking_df = (
                                df.sort_values(
                                    ["format_spread", "total_runs"],
                                    ascending=[True, False],
                                    kind="stable"
                                )
                                .reset_index(drop=True)
                            )
                            ranking_metric = "format_spread"
                            ranking_label = "Format Share Spread"

                        elif current_view == "Format Power":
                            format_totals = pd.DataFrame(
                                {
                                    "format": [
                                        "Test",
                                        "ODI",
                                        "T20I / IT20"
                                    ],
                                    "runs": [
                                        int(df["test_runs"].sum()),
                                        int(df["odi_runs"].sum()),
                                        int(df["t20i_runs"].sum())
                                    ]
                                }
                            )
                            ranking_df = df.sort_values(
                                "total_runs",
                                ascending=False,
                                kind="stable"
                            ).reset_index(drop=True)
                            ranking_metric = "total_runs"
                            ranking_label = "Combined Runs"

                        else:
                            ranking_df = df.sort_values(
                                ["total_runs", "overall_avg"],
                                ascending=[False, False],
                                kind="stable"
                            ).reset_index(drop=True)
                            ranking_metric = "total_runs"
                            ranking_label = "Combined Runs"

                        st.caption(
                            f"Active mode: **{current_view}** • "
                            f"{len(ranking_df)} players in the three-format club"
                        )

                        # ------------------------------------------------
                        # Top 3 podium
                        # ------------------------------------------------
                        st.markdown("### 🥇 Three-Format Podium")

                        podium = ranking_df.head(3)
                        medals = ["🥇", "🥈", "🥉"]
                        labels = [
                            "FORMAT MASTER",
                            "ELITE BATTER",
                            "BRONZE LEGEND"
                        ]

                        podium_cols = st.columns(len(podium))

                        for col, (_, player), medal, label in zip(
                            podium_cols,
                            podium.iterrows(),
                            medals,
                            labels
                        ):
                            name = html.escape(
                                str(player["player_name"])
                            )
                            total = int(player["total_runs"])
                            avg = float(player["overall_avg"])

                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:22px;
                                        border:1px solid #d9d9d9;
                                        border-radius:18px;
                                        text-align:center;
                                        min-height:225px;
                                        box-sizing:border-box;
                                    ">
                                        <div style="font-size:38px;">
                                            {medal}
                                        </div>
                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:0.65;
                                            margin-top:4px;
                                        ">
                                            {label}
                                        </div>
                                        <div style="
                                            font-size:18px;
                                            font-weight:700;
                                            margin:9px 0;
                                        ">
                                            {name}
                                        </div>
                                        <div style="
                                            font-size:25px;
                                            font-weight:800;
                                        ">
                                            {total:,}
                                        </div>
                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                        ">
                                            combined runs
                                        </div>
                                        <div style="
                                            margin-top:10px;
                                            font-size:12px;
                                        ">
                                            📈 Avg {avg:.2f}
                                        </div>
                                    </div>
                                    """
                                )

                        st.divider()

                        # ------------------------------------------------
                        # Interactive chart: format totals
                        # ------------------------------------------------
                        st.markdown("### 📊 Runs Across the Three Formats")

                        format_totals = pd.DataFrame(
                            {
                                "format": [
                                    "Test",
                                    "ODI",
                                    "T20I / IT20"
                                ],
                                "runs": [
                                    int(df["test_runs"].sum()),
                                    int(df["odi_runs"].sum()),
                                    int(df["t20i_runs"].sum())
                                ]
                            }
                        )

                        format_fig = px.bar(
                            format_totals,
                            x="format",
                            y="runs",
                            text="runs",
                            title="Combined runs by format",
                            labels={
                                "format": "Format",
                                "runs": "Runs"
                            }
                        )
                        format_fig.update_traces(
                            hovertemplate=(
                                "<b>%{x}</b><br>"
                                "Runs: %{y:,}<extra></extra>"
                            )
                        )
                        format_fig.update_layout(
                            height=430,
                            margin=dict(l=20, r=20, t=65, b=20),
                            showlegend=False
                        )
                        st.plotly_chart(
                            format_fig,
                            use_container_width=True,
                            key="q11_format_totals_chart"
                        )

                        # ------------------------------------------------
                        # Interactive chart: top players across formats
                        # ------------------------------------------------
                        st.markdown("### ⚔️ Format-by-Format Run Battle")

                        chart_limit = st.slider(
                            "Players shown in the comparison",
                            min_value=5,
                            max_value=min(15, len(df)),
                            value=min(10, len(df)),
                            step=1,
                            key="q11_chart_limit"
                        )

                        chart_df = ranking_df.head(chart_limit).copy()
                        chart_long = chart_df[
                            [
                                "player_name",
                                "test_runs",
                                "odi_runs",
                                "t20i_runs"
                            ]
                        ].melt(
                            id_vars="player_name",
                            var_name="format",
                            value_name="runs"
                        )

                        format_labels = {
                            "test_runs": "Test",
                            "odi_runs": "ODI",
                            "t20i_runs": "T20I / IT20"
                        }
                        chart_long["format"] = chart_long[
                            "format"
                        ].map(format_labels)

                        battle_fig = px.bar(
                            chart_long,
                            x="player_name",
                            y="runs",
                            color="format",
                            barmode="group",
                            title=(
                                f"Top {chart_limit} players — "
                                f"{current_view}"
                            ),
                            labels={
                                "player_name": "Player",
                                "runs": "Runs",
                                "format": "Format"
                            }
                        )
                        battle_fig.update_layout(
                            height=520,
                            margin=dict(l=20, r=20, t=65, b=110),
                            xaxis_tickangle=-35
                        )
                        battle_fig.update_traces(
                            hovertemplate=(
                                "<b>%{x}</b><br>"
                                "Runs: %{y:,}<extra></extra>"
                            )
                        )
                        st.plotly_chart(
                            battle_fig,
                            use_container_width=True,
                            key="q11_format_battle_chart"
                        )

                        # ------------------------------------------------
                        # Interactive chart: Test vs ODI vs T20I relationship
                        # ------------------------------------------------
                        st.markdown("### 🎯 Three-Format Performance Map")

                        scatter_fig = px.scatter(
                            df,
                            x="test_runs",
                            y="odi_runs",
                            size="t20i_runs",
                            hover_name="player_name",
                            hover_data={
                                "test_runs": ":,",
                                "odi_runs": ":,",
                                "t20i_runs": ":,",
                                "overall_avg": ":.2f",
                                "total_runs": ":,"
                            },
                            title=(
                                "Test vs ODI runs — bubble size represents "
                                "T20I / IT20 runs"
                            ),
                            labels={
                                "test_runs": "Test runs",
                                "odi_runs": "ODI runs",
                                "t20i_runs": "T20I / IT20 runs"
                            }
                        )
                        scatter_fig.update_layout(
                            height=520,
                            margin=dict(l=20, r=20, t=65, b=20)
                        )
                        st.plotly_chart(
                            scatter_fig,
                            use_container_width=True,
                            key="q11_three_format_scatter"
                        )

                        # ------------------------------------------------
                        # Player explorer
                        # ------------------------------------------------
                        st.markdown("### 🔎 Player Explorer")

                        player_options = ranking_df[
                            "player_name"
                        ].tolist()

                        selected_player = st.selectbox(
                            "Choose a player",
                            player_options,
                            key="q11_player_selector"
                        )

                        player_row = ranking_df[
                            ranking_df["player_name"] == selected_player
                        ].iloc[0]

                        detail_cols = st.columns(4)

                        with detail_cols[0]:
                            st.metric(
                                "🏏 Test Runs",
                                f"{int(player_row['test_runs']):,}"
                            )

                        with detail_cols[1]:
                            st.metric(
                                "🌍 ODI Runs",
                                f"{int(player_row['odi_runs']):,}"
                            )

                        with detail_cols[2]:
                            st.metric(
                                "⚡ T20I / IT20 Runs",
                                f"{int(player_row['t20i_runs']):,}"
                            )

                        with detail_cols[3]:
                            st.metric(
                                "📈 Overall Avg",
                                f"{float(player_row['overall_avg']):.2f}"
                            )

                        player_chart_df = pd.DataFrame(
                            {
                                "format": [
                                    "Test",
                                    "ODI",
                                    "T20I / IT20"
                                ],
                                "runs": [
                                    int(player_row["test_runs"]),
                                    int(player_row["odi_runs"]),
                                    int(player_row["t20i_runs"])
                                ]
                            }
                        )

                        player_fig = px.bar(
                            player_chart_df,
                            x="format",
                            y="runs",
                            text="runs",
                            title=f"{selected_player} — format profile",
                            labels={
                                "format": "Format",
                                "runs": "Runs"
                            }
                        )
                        player_fig.update_traces(
                            hovertemplate=(
                                "<b>%{x}</b><br>"
                                "Runs: %{y:,}<extra></extra>"
                            )
                        )
                        player_fig.update_layout(
                            height=400,
                            margin=dict(l=20, r=20, t=65, b=20),
                            showlegend=False
                        )
                        st.plotly_chart(
                            player_fig,
                            use_container_width=True,
                            key="q11_player_profile_chart"
                        )

                        st.caption(
                            "Format share spread measures the difference between "
                            "a player's largest and smallest format share. "
                            "Lower values indicate a more evenly distributed "
                            "run profile; it is a visual ranking metric, not "
                            "an official cricket statistic."
                        )

                        # ------------------------------------------------
                        # Leaderboard
                        # ------------------------------------------------
                        st.divider()
                        st.markdown("### 🏆 Complete Three-Format Leaderboard")

                        leaderboard_df = ranking_df[
                            [
                                "player_name",
                                "test_runs",
                                "odi_runs",
                                "t20i_runs",
                                "total_runs",
                                "overall_avg"
                            ]
                        ].copy()

                        leaderboard_df.insert(
                            0,
                            "Rank",
                            range(1, len(leaderboard_df) + 1)
                        )

                        leaderboard_df.columns = [
                            "Rank",
                            "Player",
                            "Test Runs",
                            "ODI Runs",
                            "T20I / IT20 Runs",
                            "Combined Runs",
                            "Overall Average"
                        ]

                        st.dataframe(
                            leaderboard_df,
                            use_container_width=True,
                            hide_index=True,
                            height=560
                        )

                        st.download_button(
                            "Download Q11 results as CSV",
                            leaderboard_df.to_csv(index=False),
                            file_name="Q11_three_format_player_performance.csv",
                            mime="text/csv"
                        )


            elif choice.startswith("Q12:"):

                st.subheader("🏠 Home vs Away Champions")

                st.caption(
                    "Compare international team wins at home and away • "
                    "Home is determined by the venue country matching the team country"
                )

                df = df.copy()

                # Normalize numeric values returned by SQLite.
                for column in [
                    "home_wins",
                    "away_wins"
                ]:
                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    ).fillna(0)

                df["home_wins"] = df["home_wins"].astype(int)
                df["away_wins"] = df["away_wins"].astype(int)

                # Build derived comparison metrics.
                df["total_wins"] = (
                    df["home_wins"] + df["away_wins"]
                )

                df["home_advantage"] = (
                    df["home_wins"] - df["away_wins"]
                )

                df["home_win_share"] = (
                    df["home_wins"]
                    .div(
                        df["total_wins"].replace(0, pd.NA)
                    )
                    .fillna(0)
                    * 100
                )

                df = (
                    df.sort_values(
                        [
                            "home_wins",
                            "away_wins",
                            "team"
                        ],
                        ascending=[
                            False,
                            False,
                            True
                        ],
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

                if df.empty:

                    st.info(
                        "No home vs away performance data is available."
                    )

                else:

                    # ------------------------------------------------
                    # Hall of Fame summary
                    # ------------------------------------------------

                    home_champion = (
                        df.sort_values(
                            [
                                "home_wins",
                                "total_wins"
                            ],
                            ascending=[
                                False,
                                False
                            ],
                            kind="stable"
                        )
                        .iloc[0]
                    )

                    away_champion = (
                        df.sort_values(
                            [
                                "away_wins",
                                "total_wins"
                            ],
                            ascending=[
                                False,
                                False
                            ],
                            kind="stable"
                        )
                        .iloc[0]
                    )

                    total_teams = len(df)
                    total_home_wins = int(
                        df["home_wins"].sum()
                    )
                    total_away_wins = int(
                        df["away_wins"].sum()
                    )
                    total_wins = int(
                        df["total_wins"].sum()
                    )

                    most_balanced = (
                        df.assign(
                            balance_gap=df["home_advantage"].abs()
                        )
                        .sort_values(
                            [
                                "balance_gap",
                                "total_wins"
                            ],
                            ascending=[
                                True,
                                False
                            ],
                            kind="stable"
                        )
                        .iloc[0]
                    )

                    home_name = html.escape(
                        str(home_champion["team"])
                    )

                    away_name = html.escape(
                        str(away_champion["team"])
                    )

                    balanced_name = html.escape(
                        str(most_balanced["team"])
                    )

                    # ------------------------------------------------
                    # Champion card
                    # ------------------------------------------------

                    st.html(
                        f"""
                        <div style="
                            padding:30px;
                            border-radius:22px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 22px 0;
                            background:
                                linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                            box-shadow:
                                0 8px 30px rgba(0,0,0,0.18);
                        ">

                            <div style="
                                font-size:52px;
                                line-height:1;
                            ">
                                🏠
                            </div>

                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:10px;
                            ">
                                HOME WIN KING
                            </div>

                            <div style="
                                font-size:32px;
                                font-weight:800;
                                margin:8px 0;
                            ">
                                {home_name}
                            </div>

                            <div style="
                                font-size:25px;
                                font-weight:800;
                            ">
                                {int(home_champion["home_wins"]):,} HOME WINS
                            </div>

                            <div style="
                                margin-top:8px;
                                opacity:0.75;
                                font-size:14px;
                            ">
                                {int(home_champion["away_wins"]):,} away wins
                                &nbsp; • &nbsp;
                                {int(home_champion["total_wins"]):,} total wins
                            </div>

                            <div style="
                                margin:18px auto 0 auto;
                                max-width:650px;
                                height:10px;
                                border-radius:10px;
                                background:rgba(255,255,255,0.10);
                                overflow:hidden;
                            ">
                                <div style="
                                    width:100%;
                                    height:100%;
                                    border-radius:10px;
                                    background:
                                        linear-gradient(
                                            90deg,
                                            #ffd700,
                                            #ff9f1c
                                        );
                                "></div>
                            </div>

                            <div style="
                                font-size:11px;
                                opacity:0.6;
                                margin-top:7px;
                            ">
                                🏆 HOME GROUND POWER
                            </div>

                        </div>
                        """
                    )

                    # ------------------------------------------------
                    # Quick stats
                    # ------------------------------------------------

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "🌍 Teams",
                            total_teams
                        )

                    with col2:
                        st.metric(
                            "🏠 Home Wins",
                            f"{total_home_wins:,}"
                        )

                    with col3:
                        st.metric(
                            "✈️ Away Wins",
                            f"{total_away_wins:,}"
                        )

                    with col4:
                        st.metric(
                            "🏆 Total Wins",
                            f"{total_wins:,}"
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Interactive view buttons
                    # ------------------------------------------------

                    st.markdown("### 🎮 Performance Mode")

                    view_options = [
                        ("home", "🏠 Home Kings"),
                        ("away", "✈️ Away Kings"),
                        ("total", "🏆 Total Wins"),
                        ("balance", "⚖️ Home Advantage")
                    ]

                    if "q12_view" not in st.session_state:
                        st.session_state["q12_view"] = "home"

                    button_cols = st.columns(
                        len(view_options)
                    )

                    for col, (view_key, label) in zip(
                        button_cols,
                        view_options
                    ):

                        with col:

                            if st.button(
                                label,
                                key=f"q12_button_{view_key}",
                                use_container_width=True,
                                type=(
                                    "primary"
                                    if st.session_state["q12_view"]
                                    == view_key
                                    else "secondary"
                                )
                            ):
                                st.session_state["q12_view"] = view_key

                    selected_view = st.session_state["q12_view"]

                    if selected_view == "home":

                        ranking_df = (
                            df.sort_values(
                                [
                                    "home_wins",
                                    "away_wins",
                                    "team"
                                ],
                                ascending=[
                                    False,
                                    False,
                                    True
                                ],
                                kind="stable"
                            )
                            .reset_index(drop=True)
                        )

                        view_title = "🏠 Home Win Rankings"
                        value_column = "home_wins"
                        value_label = "Home Wins"
                        badge = "HOME KING"

                    elif selected_view == "away":

                        ranking_df = (
                            df.sort_values(
                                [
                                    "away_wins",
                                    "home_wins",
                                    "team"
                                ],
                                ascending=[
                                    False,
                                    False,
                                    True
                                ],
                                kind="stable"
                            )
                            .reset_index(drop=True)
                        )

                        view_title = "✈️ Away Win Rankings"
                        value_column = "away_wins"
                        value_label = "Away Wins"
                        badge = "AWAY KING"

                    elif selected_view == "total":

                        ranking_df = (
                            df.sort_values(
                                [
                                    "total_wins",
                                    "home_wins",
                                    "away_wins",
                                    "team"
                                ],
                                ascending=[
                                    False,
                                    False,
                                    False,
                                    True
                                ],
                                kind="stable"
                            )
                            .reset_index(drop=True)
                        )

                        view_title = "🏆 Total Win Rankings"
                        value_column = "total_wins"
                        value_label = "Total Wins"
                        badge = "WIN CHAMPION"

                    else:

                        ranking_df = (
                            df.sort_values(
                                [
                                    "home_advantage",
                                    "total_wins",
                                    "team"
                                ],
                                ascending=[
                                    False,
                                    False,
                                    True
                                ],
                                kind="stable"
                            )
                            .reset_index(drop=True)
                        )

                        view_title = "⚖️ Home Advantage Rankings"
                        value_column = "home_advantage"
                        value_label = "Home Advantage"
                        badge = "HOME EDGE"

                    st.markdown(f"### {view_title}")

                    st.caption(
                        "Home Advantage = home wins minus away wins. "
                        "It is a comparison metric, not an official cricket statistic."
                    )

                    # ------------------------------------------------
                    # Podium
                    # ------------------------------------------------

                    podium = ranking_df.head(3)

                    if not podium.empty:

                        medals = [
                            "🥇",
                            "🥈",
                            "🥉"
                        ]

                        labels = [
                            badge,
                            "RUNNER-UP",
                            "BRONZE"
                        ]

                        podium_cols = st.columns(
                            len(podium)
                        )

                        max_value = max(
                            float(
                                ranking_df[value_column].max()
                            ),
                            1
                        )

                        for col, (_, team_row), medal, label in zip(
                            podium_cols,
                            podium.iterrows(),
                            medals,
                            labels
                        ):

                            team_name = html.escape(
                                str(team_row["team"])
                            )

                            value = float(
                                team_row[value_column]
                            )

                            power = (
                                abs(value) / max_value * 100
                            )

                            with col:

                                st.html(
                                    f"""
                                    <div style="
                                        padding:22px;
                                        border:1px solid #d9d9d9;
                                        border-radius:18px;
                                        text-align:center;
                                        min-height:250px;
                                        box-sizing:border-box;
                                    ">

                                        <div style="
                                            font-size:38px;
                                        ">
                                            {medal}
                                        </div>

                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:0.65;
                                            margin-top:4px;
                                        ">
                                            {label}
                                        </div>

                                        <div style="
                                            font-size:19px;
                                            font-weight:700;
                                            margin:9px 0;
                                        ">
                                            {team_name}
                                        </div>

                                        <div style="
                                            font-size:27px;
                                            font-weight:800;
                                        ">
                                            {value:,.0f}
                                        </div>

                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                        ">
                                            {value_label}
                                        </div>

                                        <div style="
                                            margin-top:11px;
                                            font-size:12px;
                                        ">
                                            🏠 {int(team_row["home_wins"]):,}
                                            &nbsp; • &nbsp;
                                            ✈️ {int(team_row["away_wins"]):,}
                                        </div>

                                        <div style="
                                            margin-top:13px;
                                            height:7px;
                                            border-radius:8px;
                                            background:rgba(255,255,255,0.10);
                                            overflow:hidden;
                                        ">
                                            <div style="
                                                width:{min(power, 100):.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>
                                        </div>

                                    </div>
                                    """
                                )

                    st.divider()

                    # ------------------------------------------------
                    # Interactive charts
                    # ------------------------------------------------

                    st.markdown("### 📊 Home vs Away Battle")

                    chart_limit = st.slider(
                        "Teams shown in the comparison charts",
                        min_value=5,
                        max_value=min(20, len(df)),
                        value=min(10, len(df)),
                        step=1,
                        key="q12_chart_limit"
                    )

                    chart_df = ranking_df.head(
                        chart_limit
                    ).copy()

                    chart_df = chart_df.sort_values(
                        "total_wins",
                        ascending=True
                    )

                    comparison_df = chart_df[
                        [
                            "team",
                            "home_wins",
                            "away_wins"
                        ]
                    ].melt(
                        id_vars="team",
                        value_vars=[
                            "home_wins",
                            "away_wins"
                        ],
                        var_name="location",
                        value_name="wins"
                    )

                    comparison_df["location"] = (
                        comparison_df["location"]
                        .map(
                            {
                                "home_wins": "Home",
                                "away_wins": "Away"
                            }
                        )
                    )

                    fig_comparison = px.bar(
                        comparison_df,
                        x="wins",
                        y="team",
                        color="location",
                        barmode="group",
                        orientation="h",
                        title=(
                            f"Top {chart_limit} Teams — "
                            "Home vs Away Wins"
                        ),
                        labels={
                            "wins": "Wins",
                            "team": "Team",
                            "location": "Venue"
                        },
                        hover_data={
                            "wins": True,
                            "location": True,
                            "team": True
                        }
                    )

                    fig_comparison.update_layout(
                        height=max(
                            430,
                            chart_limit * 42
                        ),
                        legend_title_text="Match Location",
                        margin={
                            "l": 10,
                            "r": 10,
                            "t": 60,
                            "b": 10
                        }
                    )

                    st.plotly_chart(
                        fig_comparison,
                        use_container_width=True
                    )

                    fig_scatter = px.scatter(
                        df,
                        x="home_wins",
                        y="away_wins",
                        size="total_wins",
                        hover_name="team",
                        hover_data={
                            "home_wins": True,
                            "away_wins": True,
                            "total_wins": True,
                            "home_advantage": True
                        },
                        title="🏠 Home Wins vs ✈️ Away Wins",
                        labels={
                            "home_wins": "Home Wins",
                            "away_wins": "Away Wins",
                            "total_wins": "Total Wins"
                        }
                    )

                    fig_scatter.update_layout(
                        height=520,
                        margin={
                            "l": 10,
                            "r": 10,
                            "t": 60,
                            "b": 10
                        }
                    )

                    st.plotly_chart(
                        fig_scatter,
                        use_container_width=True
                    )

                    # ------------------------------------------------
                    # Performance highlights
                    # ------------------------------------------------

                    st.markdown("### 🏅 Performance Highlights")

                    highlight_cols = st.columns(3)

                    with highlight_cols[0]:

                        st.html(
                            f"""
                            <div style="
                                padding:20px;
                                border:1px solid #d9d9d9;
                                border-radius:16px;
                                text-align:center;
                                min-height:155px;
                            ">
                                <div style="font-size:32px;">
                                    🏠
                                </div>
                                <div style="
                                    font-size:11px;
                                    letter-spacing:2px;
                                    opacity:0.65;
                                    margin-top:6px;
                                ">
                                    HOME LEADER
                                </div>
                                <div style="
                                    font-size:19px;
                                    font-weight:700;
                                    margin-top:8px;
                                ">
                                    {home_name}
                                </div>
                                <div style="
                                    font-size:24px;
                                    font-weight:800;
                                    margin-top:6px;
                                ">
                                    {int(home_champion["home_wins"]):,}
                                </div>
                                <div style="
                                    font-size:11px;
                                    opacity:0.65;
                                ">
                                    home wins
                                </div>
                            </div>
                            """
                        )

                    with highlight_cols[1]:

                        st.html(
                            f"""
                            <div style="
                                padding:20px;
                                border:1px solid #d9d9d9;
                                border-radius:16px;
                                text-align:center;
                                min-height:155px;
                            ">
                                <div style="font-size:32px;">
                                    ✈️
                                </div>
                                <div style="
                                    font-size:11px;
                                    letter-spacing:2px;
                                    opacity:0.65;
                                    margin-top:6px;
                                ">
                                    AWAY LEADER
                                </div>
                                <div style="
                                    font-size:19px;
                                    font-weight:700;
                                    margin-top:8px;
                                ">
                                    {away_name}
                                </div>
                                <div style="
                                    font-size:24px;
                                    font-weight:800;
                                    margin-top:6px;
                                ">
                                    {int(away_champion["away_wins"]):,}
                                </div>
                                <div style="
                                    font-size:11px;
                                    opacity:0.65;
                                ">
                                    away wins
                                </div>
                            </div>
                            """
                        )

                    with highlight_cols[2]:

                        st.html(
                            f"""
                            <div style="
                                padding:20px;
                                border:1px solid #d9d9d9;
                                border-radius:16px;
                                text-align:center;
                                min-height:155px;
                            ">
                                <div style="font-size:32px;">
                                    ⚖️
                                </div>
                                <div style="
                                    font-size:11px;
                                    letter-spacing:2px;
                                    opacity:0.65;
                                    margin-top:6px;
                                ">
                                    MOST BALANCED
                                </div>
                                <div style="
                                    font-size:19px;
                                    font-weight:700;
                                    margin-top:8px;
                                ">
                                    {balanced_name}
                                </div>
                                <div style="
                                    font-size:24px;
                                    font-weight:800;
                                    margin-top:6px;
                                ">
                                    {int(most_balanced["home_advantage"]):+,}
                                </div>
                                <div style="
                                    font-size:11px;
                                    opacity:0.65;
                                ">
                                    home advantage
                                </div>
                            </div>
                            """
                        )

                    st.divider()

                    # ------------------------------------------------
                    # Team explorer
                    # ------------------------------------------------

                    st.markdown("### 🔎 Team Explorer")

                    team_options = ranking_df[
                        "team"
                    ].astype(str).tolist()

                    selected_team = st.selectbox(
                        "Select a team",
                        team_options,
                        key="q12_team_explorer"
                    )

                    selected_row = (
                        df[
                            df["team"].astype(str)
                            == str(selected_team)
                        ]
                        .iloc[0]
                    )

                    explorer_cols = st.columns(4)

                    with explorer_cols[0]:
                        st.metric(
                            "🏠 Home Wins",
                            f"{int(selected_row['home_wins']):,}"
                        )

                    with explorer_cols[1]:
                        st.metric(
                            "✈️ Away Wins",
                            f"{int(selected_row['away_wins']):,}"
                        )

                    with explorer_cols[2]:
                        st.metric(
                            "🏆 Total Wins",
                            f"{int(selected_row['total_wins']):,}"
                        )

                    with explorer_cols[3]:
                        st.metric(
                            "⚖️ Home Advantage",
                            f"{int(selected_row['home_advantage']):+,}"
                        )

                    explorer_chart_df = pd.DataFrame(
                        {
                            "Location": [
                                "Home",
                                "Away"
                            ],
                            "Wins": [
                                int(selected_row["home_wins"]),
                                int(selected_row["away_wins"])
                            ]
                        }
                    )

                    fig_explorer = px.bar(
                        explorer_chart_df,
                        x="Location",
                        y="Wins",
                        text="Wins",
                        title=f"{selected_team} — Venue Performance",
                        labels={
                            "Wins": "Wins",
                            "Location": "Match Location"
                        }
                    )

                    fig_explorer.update_traces(
                        textposition="outside"
                    )

                    fig_explorer.update_layout(
                        height=400,
                        margin={
                            "l": 10,
                            "r": 10,
                            "t": 60,
                            "b": 10
                        }
                    )

                    st.plotly_chart(
                        fig_explorer,
                        use_container_width=True
                    )

                    st.divider()

                    # ------------------------------------------------
                    # Full leaderboard
                    # ------------------------------------------------

                    st.markdown("### ⚔️ Home vs Away Leaderboard")

                    leaderboard_df = ranking_df[
                        [
                            "team",
                            "home_wins",
                            "away_wins",
                            "total_wins",
                            "home_advantage",
                            "home_win_share"
                        ]
                    ].copy()

                    leaderboard_df.insert(
                        0,
                        "Rank",
                        range(
                            1,
                            len(leaderboard_df) + 1
                        )
                    )

                    leaderboard_df.columns = [
                        "Rank",
                        "Team",
                        "Home Wins",
                        "Away Wins",
                        "Total Wins",
                        "Home Advantage",
                        "Home Win Share %"
                    ]

                    leaderboard_df[
                        "Home Win Share %"
                    ] = leaderboard_df[
                        "Home Win Share %"
                    ].round(1)

                    st.dataframe(
                        leaderboard_df,
                        use_container_width=True,
                        hide_index=True,
                        height=560
                    )

                    st.download_button(
                        "Download Q12 results as CSV",
                        leaderboard_df.to_csv(
                            index=False
                        ),
                        file_name="Q12_home_vs_away_wins.csv",
                        mime="text/csv"
                    )


            elif choice.startswith("Q13:"):

                st.subheader("🤝 Partnership Arena")
                st.caption(
                    "100+ run batting partnerships • Explore the biggest duos, formats, "
                    "innings patterns, and partnership milestones."
                )

                df = df.copy()

                # Q13's existing SQL returns these four columns.
                # Do not require fields that the SQL does not produce.
                required_columns = [
                    "match_type",
                    "partnership",
                    "partnership_runs",
                    "innings_no",
                ]

                missing_columns = [
                    column
                    for column in required_columns
                    if column not in df.columns
                ]

                if missing_columns:
                    st.error(
                        "Q13 result is missing required columns: "
                        + ", ".join(missing_columns)
                    )
                else:
                    # Normalize the actual Q13 SQL output.
                    df["match_type"] = (
                        df["match_type"]
                        .fillna("Unknown")
                        .astype(str)
                        .str.strip()
                    )

                    df["partnership"] = (
                        df["partnership"]
                        .fillna("Unknown Partnership")
                        .astype(str)
                        .str.strip()
                    )

                    df["partnership_runs"] = pd.to_numeric(
                        df["partnership_runs"],
                        errors="coerce"
                    )

                    df["innings_no"] = pd.to_numeric(
                        df["innings_no"],
                        errors="coerce"
                    )

                    df = df.dropna(
                        subset=["partnership_runs", "innings_no"]
                    ).copy()

                    # The SQL already applies partnership_runs >= 100, but
                    # keep the same business rule defensively at the UI layer.
                    df = df[
                        df["partnership_runs"] >= 100
                    ].copy()

                    df["partnership_runs"] = (
                        df["partnership_runs"].astype(int)
                    )
                    df["innings_no"] = df["innings_no"].astype(int)

                    df = (
                        df.sort_values(
                            [
                                "partnership_runs",
                                "partnership",
                                "match_type",
                            ],
                            ascending=[False, True, True],
                            kind="stable"
                        )
                        .reset_index(drop=True)
                    )

                    if df.empty:
                        st.info(
                            "No partnerships of 100 or more runs are currently available."
                        )
                    else:
                        df["rank"] = range(1, len(df) + 1)

                        total_partnerships = len(df)
                        total_runs = int(df["partnership_runs"].sum())
                        highest_runs = int(df["partnership_runs"].max())
                        average_runs = float(df["partnership_runs"].mean())

                        champion = df.iloc[0]
                        champion_name = html.escape(
                            str(champion["partnership"])
                        )
                        champion_runs = int(champion["partnership_runs"])
                        champion_innings = int(champion["innings_no"])
                        champion_format = html.escape(
                            str(champion["match_type"])
                        )

                        # ------------------------------------------------
                        # Partnership champion
                        # ------------------------------------------------

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:
                                    linear-gradient(
                                        135deg,
                                        rgba(255,215,0,0.18),
                                        rgba(255,255,255,0.035)
                                    );
                                box-shadow:0 8px 30px rgba(0,0,0,0.18);
                            ">
                                <div style="font-size:52px;line-height:1;">👑</div>
                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    PARTNERSHIP KINGS
                                </div>
                                <div style="
                                    font-size:30px;
                                    font-weight:800;
                                    margin:10px 0;
                                ">
                                    {champion_name}
                                </div>
                                <div style="font-size:27px;font-weight:800;">
                                    {champion_runs:,} RUNS
                                </div>
                                <div style="
                                    margin-top:7px;
                                    font-size:13px;
                                    opacity:0.7;
                                ">
                                    {champion_format} • Innings {champion_innings}
                                </div>
                                <div style="
                                    margin:18px auto 0 auto;
                                    max-width:650px;
                                    height:10px;
                                    border-radius:10px;
                                    background:rgba(255,255,255,0.10);
                                    overflow:hidden;
                                ">
                                    <div style="
                                        width:100%;
                                        height:100%;
                                        border-radius:10px;
                                        background:linear-gradient(90deg,#ffd700,#ff9f1c);
                                    "></div>
                                </div>
                                <div style="font-size:11px;opacity:0.6;margin-top:7px;">
                                    🏏 100+ RUN PARTNERSHIP CLUB
                                </div>
                            </div>
                            """
                        )

                        # ------------------------------------------------
                        # Quick stats
                        # ------------------------------------------------

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "🤝 Partnerships",
                                f"{total_partnerships:,}"
                            )

                        with col2:
                            st.metric(
                                "🔥 Highest",
                                f"{highest_runs:,}"
                            )

                        with col3:
                            st.metric(
                                "📊 Average",
                                f"{average_runs:,.1f}"
                            )

                        with col4:
                            st.metric(
                                "🏏 Combined Runs",
                                f"{total_runs:,}"
                            )

                        st.divider()

                        # ------------------------------------------------
                        # Interactive controls
                        # ------------------------------------------------

                        st.markdown("### 🎮 Choose Match Type")

                        # Q13 already returns the match format as match_type.
                        # Use the actual formats in the query result instead of
                        # milestone filters that may produce empty views.
                        available_formats = [
                            value
                            for value in ["T20", "ODI", "Test"]
                            if value in set(df["match_type"])
                        ]

                        # Keep any additional real formats available in the
                        # database without creating an Unknown button.
                        additional_formats = sorted(
                            {
                                str(value).strip()
                                for value in df["match_type"].dropna().unique()
                                if str(value).strip()
                                and str(value).strip().lower() != "unknown"
                                and str(value).strip() not in available_formats
                            }
                        )

                        format_options = available_formats + additional_formats

                        button_options = [
                            ("all", "🏏 All Formats")
                        ]

                        format_icons = {
                            "T20": "⚡",
                            "ODI": "🏏",
                            "Test": "🧪",
                        }

                        for format_name in format_options:
                            icon = format_icons.get(format_name, "🏏")
                            button_options.append(
                                (
                                    format_name,
                                    f"{icon} {format_name}"
                                )
                            )

                        if "q13_view" not in st.session_state:
                            st.session_state.q13_view = "all"

                        valid_views = {
                            option[0] for option in button_options
                        }

                        if st.session_state.q13_view not in valid_views:
                            st.session_state.q13_view = "all"

                        button_cols = st.columns(len(button_options))

                        for index, (view_key, label) in enumerate(button_options):
                            with button_cols[index]:
                                selected = (
                                    st.session_state.q13_view == view_key
                                )

                                if st.button(
                                    (
                                        f"👑 {label}"
                                        if selected
                                        else label
                                    ),
                                    key=f"q13_view_{view_key}",
                                    use_container_width=True
                                ):
                                    st.session_state.q13_view = view_key
                                    st.rerun()

                        selected_view = st.session_state.q13_view

                        if selected_view == "all":
                            display_df = df.copy()
                        else:
                            display_df = df[
                                df["match_type"].eq(selected_view)
                            ].copy()

                        if display_df.empty:
                            st.info(
                                "No partnerships match this match type."
                            )
                        else:
                            # ------------------------------------------------
                            # Podium
                            # ------------------------------------------------

                            st.markdown("### 🏆 Partnership Podium")

                            podium_df = display_df.head(3).reset_index(drop=True)
                            podium_cols = st.columns(len(podium_df))

                            podium_icons = ["🥇", "🥈", "🥉"]

                            for index, (_, row) in enumerate(
                                podium_df.iterrows()
                            ):
                                with podium_cols[index]:
                                    pair_name = html.escape(
                                        str(row["partnership"])
                                    )
                                    runs_value = int(
                                        row["partnership_runs"]
                                    )
                                    format_value = html.escape(
                                        str(row["match_type"])
                                    )
                                    innings_value = int(
                                        row["innings_no"]
                                    )

                                    st.html(
                                        f"""
                                        <div style="
                                            text-align:center;
                                            padding:22px 14px;
                                            border:1px solid rgba(255,255,255,0.10);
                                            border-radius:18px;
                                            background:rgba(255,255,255,0.025);
                                        ">
                                            <div style="font-size:36px;">
                                                {podium_icons[index]}
                                            </div>
                                            <div style="
                                                font-size:17px;
                                                font-weight:800;
                                                margin-top:8px;
                                            ">
                                                {pair_name}
                                            </div>
                                            <div style="
                                                font-size:28px;
                                                font-weight:800;
                                                margin-top:8px;
                                            ">
                                                {runs_value:,}
                                            </div>
                                            <div style="font-size:11px;opacity:0.65;">
                                                RUNS
                                            </div>
                                            <div style="
                                                font-size:11px;
                                                opacity:0.65;
                                                margin-top:8px;
                                            ">
                                                {format_value} • Innings {innings_value}
                                            </div>
                                        </div>
                                        """
                                    )

                            st.divider()

                            # ------------------------------------------------
                            # Interactive chart
                            # ------------------------------------------------

                            chart_df = display_df.head(15).copy()
                            chart_df["pair_label"] = chart_df[
                                "partnership"
                            ].astype(str)

                            chart_df = chart_df.sort_values(
                                "partnership_runs",
                                ascending=True,
                                kind="stable"
                            )

                            fig = px.bar(
                                chart_df,
                                x="partnership_runs",
                                y="pair_label",
                                orientation="h",
                                text="partnership_runs",
                                title="Top Partnership Combos",
                                labels={
                                    "partnership_runs": "Partnership Runs",
                                    "pair_label": "Partnership"
                                },
                                hover_data={
                                    "match_type": True,
                                    "innings_no": True,
                                    "partnership_runs": True,
                                }
                            )

                            fig.update_traces(
                                texttemplate="%{text}",
                                textposition="outside"
                            )

                            fig.update_layout(
                                height=max(420, len(chart_df) * 34),
                                margin=dict(l=10, r=40, t=60, b=20),
                                yaxis={
                                    "categoryorder": "total ascending"
                                }
                            )

                            st.plotly_chart(
                                fig,
                                use_container_width=True,
                                key="q13_top_partnerships_chart"
                            )

                            # ------------------------------------------------
                            # Partnership distribution by innings
                            # ------------------------------------------------

                            innings_df = (
                                display_df["innings_no"]
                                .value_counts()
                                .sort_index()
                                .rename_axis("Innings")
                                .reset_index(name="Partnerships")
                            )

                            fig_innings = px.bar(
                                innings_df,
                                x="Innings",
                                y="Partnerships",
                                text="Partnerships",
                                title="100+ Partnerships by Innings",
                                labels={
                                    "Partnerships": "Qualifying Partnerships",
                                    "Innings": "Innings Number"
                                }
                            )

                            fig_innings.update_traces(
                                textposition="outside"
                            )

                            fig_innings.update_layout(
                                height=400,
                                margin=dict(l=10, r=10, t=60, b=20)
                            )

                            st.plotly_chart(
                                fig_innings,
                                use_container_width=True,
                                key="q13_innings_chart"
                            )

                            # ------------------------------------------------
                            # Format breakdown
                            # ------------------------------------------------

                            format_df = (
                                display_df.groupby("match_type")
                                .agg(
                                    Partnerships=(
                                        "partnership",
                                        "count"
                                    ),
                                    Total_Runs=(
                                        "partnership_runs",
                                        "sum"
                                    ),
                                    Best_Partnership=(
                                        "partnership_runs",
                                        "max"
                                    )
                                )
                                .reset_index()
                            )

                            fig_format = px.bar(
                                format_df,
                                x="match_type",
                                y="Partnerships",
                                text="Partnerships",
                                title="100+ Partnerships by Match Type",
                                labels={
                                    "match_type": "Match Type",
                                    "Partnerships": "Partnership Count"
                                },
                                hover_data={
                                    "Total_Runs": True,
                                    "Best_Partnership": True
                                }
                            )

                            fig_format.update_traces(
                                textposition="outside"
                            )

                            fig_format.update_layout(
                                height=400,
                                margin=dict(l=10, r=10, t=60, b=20)
                            )

                            st.plotly_chart(
                                fig_format,
                                use_container_width=True,
                                key="q13_format_chart"
                            )

                            st.divider()

                            # ------------------------------------------------
                            # Partnership explorer
                            # ------------------------------------------------

                            st.markdown("### 🔎 Partnership Explorer")

                            explorer_options = [
                                f"{row['partnership']} — {int(row['partnership_runs']):,} runs"
                                for _, row in display_df.head(50).iterrows()
                            ]

                            selected_explorer = st.selectbox(
                                "Select a partnership",
                                explorer_options,
                                key="q13_partnership_explorer"
                            )

                            selected_index = explorer_options.index(
                                selected_explorer
                            )
                            selected_row = display_df.head(50).iloc[
                                selected_index
                            ]

                            explorer_cols = st.columns(4)

                            with explorer_cols[0]:
                                st.metric(
                                    "🤝 Partnership",
                                    str(selected_row["partnership"])
                                )

                            with explorer_cols[1]:
                                st.metric(
                                    "🔥 Runs",
                                    f"{int(selected_row['partnership_runs']):,}"
                                )

                            with explorer_cols[2]:
                                st.metric(
                                    "🏏 Match Type",
                                    str(selected_row["match_type"])
                                )

                            with explorer_cols[3]:
                                st.metric(
                                    "📖 Innings",
                                    str(int(selected_row["innings_no"]))
                                )

                            st.caption(
                                "Batting positions and match ID are not included in the current Q13 SQL result, "
                                "so the explorer uses the fields actually returned by the query."
                            )

                            st.divider()

                            # ------------------------------------------------
                            # XP-style leaderboard
                            # ------------------------------------------------

                            st.markdown("### ⚔️ Partnership Leaderboard")

                            leaderboard_df = display_df.copy()
                            max_runs = max(
                                int(leaderboard_df["partnership_runs"].max()),
                                1
                            )

                            for rank, (_, row) in enumerate(
                                leaderboard_df.head(20).iterrows(),
                                start=1
                            ):
                                pair_name = html.escape(
                                    str(row["partnership"])
                                )
                                pair_runs = int(
                                    row["partnership_runs"]
                                )
                                power = min(
                                    100,
                                    (pair_runs / max_runs) * 100
                                )
                                innings_number = int(row["innings_no"])
                                format_name = html.escape(
                                    str(row["match_type"])
                                )

                                if rank == 1:
                                    rank_icon = "🥇"
                                    badge = "LEGENDARY DUO"
                                elif rank == 2:
                                    rank_icon = "🥈"
                                    badge = "ELITE DUO"
                                elif rank == 3:
                                    rank_icon = "🥉"
                                    badge = "ELITE DUO"
                                elif rank <= 5:
                                    rank_icon = "🔥"
                                    badge = "TOP 5"
                                else:
                                    rank_icon = "⚡"
                                    badge = "100+ CLUB"

                                st.html(
                                    f"""
                                    <div style="
                                        padding:15px 18px;
                                        border:1px solid rgba(255,255,255,0.10);
                                        border-radius:14px;
                                        margin:8px 0;
                                        background:rgba(255,255,255,0.025);
                                    ">
                                        <div style="
                                            display:flex;
                                            align-items:center;
                                            gap:14px;
                                            flex-wrap:wrap;
                                        ">
                                            <div style="
                                                width:38px;
                                                text-align:center;
                                                font-size:22px;
                                            ">
                                                {rank_icon}
                                            </div>
                                            <div style="min-width:210px;">
                                                <div style="font-size:15px;font-weight:700;">
                                                    #{rank} {pair_name}
                                                </div>
                                                <div style="font-size:10px;letter-spacing:1px;opacity:0.55;margin-top:3px;">
                                                    {badge}
                                                </div>
                                            </div>
                                            <div style="flex:1;min-width:140px;">
                                                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:5px;">
                                                    <span>PARTNERSHIP POWER</span>
                                                    <span>{power:.1f}%</span>
                                                </div>
                                                <div style="height:8px;border-radius:8px;background:rgba(255,255,255,0.08);overflow:hidden;">
                                                    <div style="width:{power:.1f}%;height:100%;border-radius:8px;background:linear-gradient(90deg,#ffd700,#ff9f1c);"></div>
                                                </div>
                                            </div>
                                            <div style="min-width:100px;text-align:right;">
                                                <div style="font-size:19px;font-weight:800;">
                                                    {pair_runs:,}
                                                </div>
                                                <div style="font-size:10px;opacity:0.55;">RUNS</div>
                                            </div>
                                            <div style="min-width:130px;text-align:right;font-size:11px;opacity:0.75;">
                                                {format_name}
                                                <br>
                                                Innings {innings_number}
                                            </div>
                                        </div>
                                    </div>
                                    """
                                )

                            st.divider()

                            # ------------------------------------------------
                            # Detailed results
                            # ------------------------------------------------

                            st.markdown("### 📋 Detailed Partnership Records")

                            table_df = display_df[
                                [
                                    "rank",
                                    "match_type",
                                    "partnership",
                                    "partnership_runs",
                                    "innings_no",
                                ]
                            ].copy()

                            table_df.columns = [
                                "Rank",
                                "Match Type",
                                "Partnership",
                                "Partnership Runs",
                                "Innings",
                            ]

                            st.dataframe(
                                table_df,
                                use_container_width=True,
                                hide_index=True,
                                height=500
                            )

                            st.download_button(
                                "Download Q13 results as CSV",
                                display_df.to_csv(index=False),
                                file_name="Q13_partnerships.csv",
                                mime="text/csv"
                            )



            elif choice.startswith("Q14:"):

                st.subheader("🎯 Bowling Venue Arena")
                st.caption(
                    "Bowlers with 3+ qualifying matches at a venue • "
                    "4-over minimum in every included match • "
                    "Compare economy, wickets, and venue experience."
                )

                df = df.copy()

                required_columns = [
                    "player_name",
                    "venue_name",
                    "avg_economy",
                    "total_wickets",
                    "matches_played",
                ]

                missing_columns = [
                    column
                    for column in required_columns
                    if column not in df.columns
                ]

                if missing_columns:

                    st.error(
                        "Q14 result is missing required columns: "
                        + ", ".join(missing_columns)
                    )

                else:

                    df["player_name"] = (
                        df["player_name"]
                        .fillna("Unknown Player")
                        .astype(str)
                        .str.strip()
                    )

                    df["venue_name"] = (
                        df["venue_name"]
                        .fillna("Unknown Venue")
                        .astype(str)
                        .str.strip()
                    )

                    for column in [
                        "avg_economy",
                        "total_wickets",
                        "matches_played",
                    ]:
                        df[column] = pd.to_numeric(
                            df[column],
                            errors="coerce"
                        )

                    df = df.dropna(
                        subset=[
                            "avg_economy",
                            "total_wickets",
                            "matches_played",
                        ]
                    ).copy()

                    df = df[
                        (df["matches_played"] >= 3)
                        & (df["avg_economy"] >= 0)
                    ].copy()

                    df["avg_economy"] = df["avg_economy"].round(2)
                    df["total_wickets"] = df["total_wickets"].astype(int)
                    df["matches_played"] = df["matches_played"].astype(int)

                    df = (
                        df.sort_values(
                            [
                                "avg_economy",
                                "total_wickets",
                                "player_name",
                            ],
                            ascending=[True, False, True],
                            kind="stable"
                        )
                        .reset_index(drop=True)
                    )

                    if df.empty:

                        st.info(
                            "No qualifying bowling performances are available."
                        )

                    else:

                        economy_champion = df.iloc[0]

                        wicket_champion = (
                            df.sort_values(
                                [
                                    "total_wickets",
                                    "avg_economy",
                                    "player_name",
                                ],
                                ascending=[False, True, True],
                                kind="stable"
                            )
                            .iloc[0]
                        )

                        experience_champion = (
                            df.sort_values(
                                [
                                    "matches_played",
                                    "total_wickets",
                                    "avg_economy",
                                ],
                                ascending=[False, False, True],
                                kind="stable"
                            )
                            .iloc[0]
                        )

                        venue_count = int(df["venue_name"].nunique())
                        bowler_count = int(df["player_name"].nunique())
                        performance_count = len(df)
                        total_wickets = int(df["total_wickets"].sum())
                        average_economy = float(df["avg_economy"].mean())

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:
                                    linear-gradient(
                                        135deg,
                                        rgba(255,215,0,0.18),
                                        rgba(255,255,255,0.035)
                                    );
                                box-shadow:0 8px 30px rgba(0,0,0,0.18);
                            ">
                                <div style="font-size:52px;line-height:1;">👑</div>
                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    ECONOMY KING
                                </div>
                                <div style="
                                    font-size:31px;
                                    font-weight:800;
                                    margin:9px 0;
                                ">
                                    {html.escape(str(economy_champion["player_name"]))}
                                </div>
                                <div style="
                                    font-size:24px;
                                    font-weight:800;
                                ">
                                    {float(economy_champion["avg_economy"]):.2f}
                                </div>
                                <div style="
                                    margin-top:5px;
                                    font-size:13px;
                                    opacity:0.7;
                                ">
                                    economy at {html.escape(str(economy_champion["venue_name"]))}
                                    &nbsp; • &nbsp;
                                    {int(economy_champion["matches_played"])} matches
                                </div>
                                <div style="
                                    margin:18px auto 0 auto;
                                    max-width:650px;
                                    height:10px;
                                    border-radius:10px;
                                    background:rgba(255,255,255,0.10);
                                    overflow:hidden;
                                ">
                                    <div style="
                                        width:100%;
                                        height:100%;
                                        border-radius:10px;
                                        background:
                                            linear-gradient(
                                                90deg,
                                                #ffd700,
                                                #ff9f1c
                                            );
                                    "></div>
                                </div>
                                <div style="
                                    font-size:11px;
                                    opacity:0.6;
                                    margin-top:7px;
                                ">
                                    🎯 LOWEST QUALIFYING ECONOMY
                                </div>
                            </div>
                            """
                        )

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "🎯 Bowling Performances",
                                performance_count
                            )

                        with col2:
                            st.metric(
                                "👥 Bowlers",
                                bowler_count
                            )

                        with col3:
                            st.metric(
                                "🏟️ Venues",
                                venue_count
                            )

                        with col4:
                            st.metric(
                                "⚡ Total Wickets",
                                f"{total_wickets:,}"
                            )

                        st.divider()

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "🎯 Best Economy",
                                f"{float(economy_champion['avg_economy']):.2f}"
                            )

                        with col2:
                            st.metric(
                                "🔥 Most Wickets",
                                f"{int(wicket_champion['total_wickets'])}"
                            )

                        with col3:
                            st.metric(
                                "🧱 Most Matches at Venue",
                                f"{int(experience_champion['matches_played'])}"
                            )

                        st.divider()

                        st.markdown("### 🎮 Choose Your Bowling Mode")

                        button_options = [
                            ("economy", "🎯 Best Economy"),
                            ("wickets", "🔥 Most Wickets"),
                            ("matches", "🧱 Most Matches"),
                            ("all", "🏟️ All Performances"),
                        ]

                        if "q14_view" not in st.session_state:
                            st.session_state.q14_view = "economy"

                        valid_views = {
                            option[0]
                            for option in button_options
                        }

                        if st.session_state.q14_view not in valid_views:
                            st.session_state.q14_view = "economy"

                        button_cols = st.columns(len(button_options))

                        for index, (view_key, label) in enumerate(
                            button_options
                        ):
                            with button_cols[index]:

                                selected = (
                                    st.session_state.q14_view == view_key
                                )

                                if st.button(
                                    f"👑 {label}" if selected else label,
                                    key=f"q14_view_{view_key}",
                                    use_container_width=True
                                ):
                                    st.session_state.q14_view = view_key
                                    st.rerun()

                        selected_view = st.session_state.q14_view

                        if selected_view == "wickets":
                            display_df = (
                                df.sort_values(
                                    [
                                        "total_wickets",
                                        "avg_economy",
                                        "player_name",
                                    ],
                                    ascending=[False, True, True],
                                    kind="stable"
                                )
                                .reset_index(drop=True)
                            )

                        elif selected_view == "matches":
                            display_df = (
                                df.sort_values(
                                    [
                                        "matches_played",
                                        "total_wickets",
                                        "avg_economy",
                                    ],
                                    ascending=[False, False, True],
                                    kind="stable"
                                )
                                .reset_index(drop=True)
                            )

                        elif selected_view == "all":
                            display_df = df.copy()

                        else:
                            display_df = (
                                df.sort_values(
                                    [
                                        "avg_economy",
                                        "total_wickets",
                                        "player_name",
                                    ],
                                    ascending=[True, False, True],
                                    kind="stable"
                                )
                                .reset_index(drop=True)
                            )

                        st.markdown("### 🥇 Venue Bowling Podium")

                        podium = display_df.head(3)
                        medals = ["🥇", "🥈", "🥉"]
                        labels = ["CHAMPION", "RUNNER-UP", "BRONZE"]
                        podium_cols = st.columns(max(len(podium), 1))

                        if selected_view == "wickets":
                            max_metric = max(
                                float(display_df["total_wickets"].max()),
                                1
                            )
                        elif selected_view == "matches":
                            max_metric = max(
                                float(display_df["matches_played"].max()),
                                1
                            )
                        else:
                            best_economy = max(
                                float(display_df["avg_economy"].min()),
                                0.01
                            )
                            max_metric = max(
                                float(display_df["avg_economy"].max()),
                                best_economy
                            )

                        for col, (_, row), medal, label in zip(
                            podium_cols,
                            podium.iterrows(),
                            medals,
                            labels
                        ):

                            if selected_view == "wickets":
                                metric_value = int(row["total_wickets"])
                                metric_label = "wickets"
                                power = (
                                    float(row["total_wickets"])
                                    / max_metric
                                    * 100
                                )

                            elif selected_view == "matches":
                                metric_value = int(row["matches_played"])
                                metric_label = "matches"
                                power = (
                                    float(row["matches_played"])
                                    / max_metric
                                    * 100
                                )

                            else:
                                metric_value = float(row["avg_economy"])
                                metric_label = "economy"
                                power = (
                                    best_economy
                                    / max(float(row["avg_economy"]), 0.01)
                                    * 100
                                )

                            power = min(max(power, 0), 100)

                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:22px;
                                        border:1px solid #d9d9d9;
                                        border-radius:18px;
                                        text-align:center;
                                        min-height:255px;
                                        box-sizing:border-box;
                                    ">
                                        <div style="font-size:38px;">{medal}</div>
                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:0.65;
                                            margin-top:4px;
                                        ">
                                            {label}
                                        </div>
                                        <div style="
                                            font-size:19px;
                                            font-weight:700;
                                            margin:9px 0;
                                        ">
                                            {html.escape(str(row["player_name"]))}
                                        </div>
                                        <div style="
                                            font-size:26px;
                                            font-weight:800;
                                        ">
                                            {metric_value:.2f}
                                        </div>
                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                        ">
                                            {metric_label}
                                        </div>
                                        <div style="
                                            margin-top:8px;
                                            font-size:11px;
                                            opacity:0.65;
                                        ">
                                            🏟️ {html.escape(str(row["venue_name"]))}
                                        </div>
                                        <div style="
                                            margin-top:6px;
                                            font-size:11px;
                                            opacity:0.65;
                                        ">
                                            🔥 {int(row["total_wickets"])} wickets
                                            &nbsp; • &nbsp;
                                            {int(row["matches_played"])} matches
                                        </div>
                                        <div style="
                                            margin-top:13px;
                                            height:7px;
                                            border-radius:8px;
                                            background:rgba(255,255,255,0.10);
                                            overflow:hidden;
                                        ">
                                            <div style="
                                                width:{power:.1f}%;
                                                height:100%;
                                                border-radius:8px;
                                                background:
                                                    linear-gradient(
                                                        90deg,
                                                        #ffd700,
                                                        #ff9f1c
                                                    );
                                            "></div>
                                        </div>
                                    </div>
                                    """
                                )

                        st.divider()

                        st.markdown("### 📊 Bowling Performance Chart")
                        st.caption("Only the selected chart is rendered to keep Q14 fast.")

                        if selected_view == "economy":
                            chart_df = (
                                df.sort_values(
                                    ["avg_economy", "total_wickets"],
                                    ascending=[True, False],
                                    kind="stable"
                                )
                                .head(12)
                                .sort_values("avg_economy", ascending=False)
                            )
                            fig = px.bar(
                                chart_df,
                                x="avg_economy",
                                y="player_name",
                                orientation="h",
                                hover_data=["venue_name", "total_wickets", "matches_played"],
                                title="🎯 Best Venue Economy"
                            )
                            fig.update_layout(
                                yaxis_title="Bowler",
                                xaxis_title="Average Economy",
                                height=450,
                                showlegend=False
                            )

                        elif selected_view == "wickets":
                            chart_df = (
                                df.sort_values(
                                    ["total_wickets", "avg_economy"],
                                    ascending=[False, True],
                                    kind="stable"
                                )
                                .head(12)
                                .sort_values("total_wickets")
                            )
                            fig = px.bar(
                                chart_df,
                                x="total_wickets",
                                y="player_name",
                                orientation="h",
                                hover_data=["venue_name", "avg_economy", "matches_played"],
                                title="🔥 Most Venue Wickets"
                            )
                            fig.update_layout(
                                yaxis_title="Bowler",
                                xaxis_title="Total Wickets",
                                height=450,
                                showlegend=False
                            )

                        elif selected_view == "matches":
                            chart_df = (
                                df.sort_values(
                                    ["matches_played", "total_wickets"],
                                    ascending=[False, False],
                                    kind="stable"
                                )
                                .head(12)
                                .sort_values("matches_played")
                            )
                            fig = px.bar(
                                chart_df,
                                x="matches_played",
                                y="player_name",
                                orientation="h",
                                hover_data=["venue_name", "avg_economy", "total_wickets"],
                                title="🧱 Most Venue Matches"
                            )
                            fig.update_layout(
                                yaxis_title="Bowler",
                                xaxis_title="Matches Played",
                                height=450,
                                showlegend=False
                            )

                        else:
                            fig = px.scatter(
                                df,
                                x="avg_economy",
                                y="total_wickets",
                                size="matches_played",
                                hover_name="player_name",
                                hover_data=["venue_name", "matches_played"],
                                title="⚔️ Economy vs Wicket Power"
                            )
                            fig.update_layout(
                                xaxis_title="Average Economy — lower is better",
                                yaxis_title="Total Wickets",
                                height=500,
                                showlegend=False
                            )

                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config={"displayModeBar": False}
                        )

                        st.divider()

                        st.markdown("### 🔎 Venue Bowling Explorer")

                        explorer_options = [
                            f"{row['player_name']} — {row['venue_name']}"
                            for _, row in df.iterrows()
                        ]

                        selected_explorer = st.selectbox(
                            "Choose a bowler + venue",
                            explorer_options,
                            key="q14_explorer"
                        )

                        selected_index = explorer_options.index(
                            selected_explorer
                        )
                        selected_row = df.iloc[selected_index]

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "🎯 Economy",
                                f"{float(selected_row['avg_economy']):.2f}"
                            )

                        with col2:
                            st.metric(
                                "🔥 Wickets",
                                int(selected_row["total_wickets"])
                            )

                        with col3:
                            st.metric(
                                "🗓️ Matches",
                                int(selected_row["matches_played"])
                            )

                        with col4:
                            st.metric(
                                "🏟️ Venue",
                                str(selected_row["venue_name"])
                            )

                        st.html(
                            f"""
                            <div style="
                                margin-top:15px;
                                padding:20px;
                                border:1px solid rgba(255,255,255,0.10);
                                border-radius:16px;
                                text-align:center;
                            ">
                                <div style="
                                    font-size:12px;
                                    letter-spacing:2px;
                                    opacity:0.6;
                                ">
                                    VENUE PERFORMANCE CARD
                                </div>
                                <div style="
                                    font-size:24px;
                                    font-weight:800;
                                    margin-top:8px;
                                ">
                                    {html.escape(str(selected_row["player_name"]))}
                                </div>
                                <div style="
                                    font-size:14px;
                                    opacity:0.75;
                                    margin-top:5px;
                                ">
                                    {html.escape(str(selected_row["venue_name"]))}
                                </div>
                                <div style="
                                    margin-top:16px;
                                    font-size:13px;
                                ">
                                    🎯 {float(selected_row["avg_economy"]):.2f} economy
                                    &nbsp; • &nbsp;
                                    🔥 {int(selected_row["total_wickets"])} wickets
                                    &nbsp; • &nbsp;
                                    🗓️ {int(selected_row["matches_played"])} matches
                                </div>
                            </div>
                            """
                        )

                        st.divider()

                        st.markdown("### ⚔️ Venue Bowling Battle")

                        st.caption(
                            "Economy Power is a visual ranking aid: lower economy "
                            "rates receive higher power. It is not an official statistic."
                        )

                        leaderboard_df = display_df.head(20).copy()

                        best_economy = max(
                            float(leaderboard_df["avg_economy"].min()),
                            0.01
                        )
                        worst_economy = max(
                            float(leaderboard_df["avg_economy"].max()),
                            best_economy
                        )

                        for rank, (_, row) in enumerate(
                            leaderboard_df.iterrows(),
                            start=1
                        ):

                            economy = float(row["avg_economy"])
                            wickets = int(row["total_wickets"])
                            matches = int(row["matches_played"])

                            if worst_economy == best_economy:
                                economy_power = 100
                            else:
                                economy_power = (
                                    (worst_economy - economy)
                                    / (worst_economy - best_economy)
                                    * 100
                                )

                            economy_power = min(
                                max(economy_power, 0),
                                100
                            )

                            if rank == 1:
                                rank_icon = "👑"
                                badge = "VENUE KING"
                            elif rank == 2:
                                rank_icon = "🥈"
                                badge = "ELITE"
                            elif rank == 3:
                                rank_icon = "🥉"
                                badge = "ELITE"
                            elif rank <= 5:
                                rank_icon = "🔥"
                                badge = "TOP 5"
                            else:
                                rank_icon = "⚡"
                                badge = "QUALIFIED"

                            st.html(
                                f"""
                                <div style="
                                    padding:15px 18px;
                                    border:1px solid rgba(
                                        255,255,255,0.10
                                    );
                                    border-radius:14px;
                                    margin:8px 0;
                                    background:rgba(
                                        255,255,255,0.025
                                    );
                                ">
                                    <div style="
                                        display:flex;
                                        align-items:center;
                                        gap:14px;
                                    ">
                                        <div style="
                                            width:38px;
                                            text-align:center;
                                            font-size:22px;
                                        ">
                                            {rank_icon}
                                        </div>
                                        <div style="min-width:185px;">
                                            <div style="
                                                font-size:15px;
                                                font-weight:700;
                                            ">
                                                #{rank} {html.escape(str(row["player_name"]))}
                                            </div>
                                            <div style="
                                                font-size:10px;
                                                letter-spacing:1px;
                                                opacity:0.55;
                                                margin-top:3px;
                                            ">
                                                {badge}
                                            </div>
                                            <div style="
                                                font-size:10px;
                                                opacity:0.55;
                                                margin-top:3px;
                                            ">
                                                🏟️ {html.escape(str(row["venue_name"]))}
                                            </div>
                                        </div>
                                        <div style="
                                            flex:1;
                                            min-width:120px;
                                        ">
                                            <div style="
                                                display:flex;
                                                justify-content:space-between;
                                                font-size:11px;
                                                margin-bottom:5px;
                                            ">
                                                <span>ECONOMY POWER</span>
                                                <span>{economy_power:.1f}%</span>
                                            </div>
                                            <div style="
                                                height:8px;
                                                border-radius:8px;
                                                background:
                                                    rgba(
                                                        255,255,255,0.08
                                                    );
                                                overflow:hidden;
                                            ">
                                                <div style="
                                                    width:{economy_power:.1f}%;
                                                    height:100%;
                                                    border-radius:8px;
                                                    background:
                                                        linear-gradient(
                                                            90deg,
                                                            #ffd700,
                                                            #ff9f1c
                                                        );
                                                "></div>
                                            </div>
                                        </div>
                                        <div style="
                                            min-width:90px;
                                            text-align:right;
                                        ">
                                            <div style="
                                                font-size:18px;
                                                font-weight:800;
                                            ">
                                                {economy:.2f}
                                            </div>
                                            <div style="
                                                font-size:10px;
                                                opacity:0.55;
                                            ">
                                                ECON
                                            </div>
                                        </div>
                                        <div style="
                                            min-width:115px;
                                            text-align:right;
                                            font-size:12px;
                                            opacity:0.8;
                                        ">
                                            🔥 {wickets}
                                            &nbsp; • &nbsp;
                                            🗓️ {matches}
                                        </div>
                                    </div>
                                </div>
                                """
                            )

                        st.divider()

                        st.markdown("### 📋 Complete Venue Bowling Stats")

                        table_df = display_df[
                            [
                                "player_name",
                                "venue_name",
                                "avg_economy",
                                "total_wickets",
                                "matches_played",
                            ]
                        ].copy()

                        table_df.insert(
                            0,
                            "Rank",
                            range(1, len(table_df) + 1)
                        )

                        table_df.columns = [
                            "Rank",
                            "Player",
                            "Venue",
                            "Average Economy",
                            "Total Wickets",
                            "Matches Played",
                        ]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                            height=600
                        )

                        st.download_button(
                            "Download Q14 results as CSV",
                            display_df.to_csv(index=False),
                            file_name="Q14_bowling_by_venue.csv",
                            mime="text/csv"
                        )



            elif choice.startswith("Q15:"):

                st.subheader("🔥 Close Match Warriors")

                st.caption(
                    "Players who consistently perform in close matches • "
                    "Less than 50 runs or less than 5 wickets"
                )

                df = df.copy()

                required_columns = [
                    "player_name",
                    "avg_runs_close_matches",
                    "close_matches_played",
                    "close_matches_team_won",
                ]

                missing_columns = [
                    column
                    for column in required_columns
                    if column not in df.columns
                ]

                if missing_columns:
                    st.error(
                        "Q15 result is missing required columns: "
                        + ", ".join(missing_columns)
                    )

                else:
                    # Normalize only the fields needed by the dashboard.
                    numeric_columns = [
                        "avg_runs_close_matches",
                        "close_matches_played",
                        "close_matches_team_won",
                    ]

                    for column in numeric_columns:
                        df[column] = pd.to_numeric(
                            df[column],
                            errors="coerce"
                        )

                    df = df.dropna(
                        subset=[
                            "player_name",
                            "avg_runs_close_matches",
                            "close_matches_played",
                            "close_matches_team_won",
                        ]
                    ).copy()

                    df["close_matches_played"] = (
                        df["close_matches_played"]
                        .astype(int)
                    )

                    df["close_matches_team_won"] = (
                        df["close_matches_team_won"]
                        .astype(int)
                    )

                    # Win rate is a derived dashboard metric:
                    # team wins when the player batted / close matches played.
                    df["team_win_rate"] = (
                        df["close_matches_team_won"]
                        .div(
                            df["close_matches_played"]
                            .replace(0, pd.NA)
                        )
                        .mul(100)
                        .fillna(0)
                    )

                    df = (
                        df.sort_values(
                            "avg_runs_close_matches",
                            ascending=False,
                            kind="stable"
                        )
                        .reset_index(drop=True)
                    )

                    if df.empty:
                        st.info(
                            "No close-match player data is available."
                        )

                    else:
                        champion = df.iloc[0]

                        champion_name = html.escape(
                            str(champion["player_name"])
                        )

                        champion_avg = float(
                            champion["avg_runs_close_matches"]
                        )

                        champion_matches = int(
                            champion["close_matches_played"]
                        )

                        champion_wins = int(
                            champion["close_matches_team_won"]
                        )

                        champion_win_rate = float(
                            champion["team_win_rate"]
                        )

                        total_players = len(df)
                        total_close_matches = int(
                            df["close_matches_played"].sum()
                        )
                        total_team_wins = int(
                            df["close_matches_team_won"].sum()
                        )

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:
                                    linear-gradient(
                                        135deg,
                                        rgba(255,215,0,0.18),
                                        rgba(255,255,255,0.035)
                                    );
                                box-shadow:
                                    0 8px 30px rgba(0,0,0,0.18);
                            ">
                                <div style="
                                    font-size:52px;
                                    line-height:1;
                                ">
                                    🏆
                                </div>

                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    CLOSE MATCH KING
                                </div>

                                <div style="
                                    font-size:32px;
                                    font-weight:800;
                                    margin:8px 0;
                                ">
                                    {champion_name}
                                </div>

                                <div style="
                                    font-size:25px;
                                    font-weight:800;
                                ">
                                    {champion_avg:.2f} RUNS
                                </div>

                                <div style="
                                    margin-top:8px;
                                    font-size:14px;
                                    opacity:0.75;
                                ">
                                    {champion_matches} close matches
                                    &nbsp; • &nbsp;
                                    {champion_wins} team wins
                                    &nbsp; • &nbsp;
                                    {champion_win_rate:.1f}% win rate
                                </div>
                            </div>
                            """
                        )

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric(
                                "👥 Players",
                                total_players
                            )

                        with col2:
                            st.metric(
                                "🔥 Best Avg Runs",
                                f"{champion_avg:.2f}"
                            )

                        with col3:
                            st.metric(
                                "⚔️ Close Matches",
                                total_close_matches
                            )

                        with col4:
                            st.metric(
                                "🏆 Team Wins",
                                total_team_wins
                            )

                        st.divider()

                        st.markdown("### 🎮 Choose Your Battle Mode")

                        button_options = [
                            ("average", "🔥 Avg Runs"),
                            ("wins", "🏆 Team Wins"),
                            ("matches", "⚔️ Matches Played"),
                            ("win_rate", "📈 Win Rate"),
                        ]

                        if "q15_view" not in st.session_state:
                            st.session_state["q15_view"] = "average"

                        button_cols = st.columns(4)

                        for col, (view_key, label) in zip(
                            button_cols,
                            button_options
                        ):
                            with col:
                                if st.button(
                                    label,
                                    key=f"q15_{view_key}_button",
                                    use_container_width=True
                                ):
                                    st.session_state["q15_view"] = (
                                        view_key
                                    )

                        active_view = st.session_state["q15_view"]

                        if active_view == "average":
                            display_df = (
                                df.sort_values(
                                    "avg_runs_close_matches",
                                    ascending=False
                                )
                                .head(15)
                                .copy()
                            )
                            metric_column = "avg_runs_close_matches"
                            chart_title = (
                                "🔥 Top Players by Average Runs"
                            )
                            y_title = "Average Runs"
                            chart_df = display_df.rename(
                                columns={
                                    "avg_runs_close_matches": "value"
                                }
                            )

                        elif active_view == "wins":
                            display_df = (
                                df.sort_values(
                                    "close_matches_team_won",
                                    ascending=False
                                )
                                .head(15)
                                .copy()
                            )
                            metric_column = "close_matches_team_won"
                            chart_title = (
                                "🏆 Top Players by Team Wins in Close Matches"
                            )
                            y_title = "Team Wins"
                            chart_df = display_df.rename(
                                columns={
                                    "close_matches_team_won": "value"
                                }
                            )

                        elif active_view == "matches":
                            display_df = (
                                df.sort_values(
                                    "close_matches_played",
                                    ascending=False
                                )
                                .head(15)
                                .copy()
                            )
                            metric_column = "close_matches_played"
                            chart_title = (
                                "⚔️ Players with Most Close Matches"
                            )
                            y_title = "Close Matches"
                            chart_df = display_df.rename(
                                columns={
                                    "close_matches_played": "value"
                                }
                            )

                        else:
                            display_df = (
                                df.sort_values(
                                    "team_win_rate",
                                    ascending=False
                                )
                                .head(15)
                                .copy()
                            )
                            metric_column = "team_win_rate"
                            chart_title = (
                                "📈 Best Team Win Rate When Batting"
                            )
                            y_title = "Win Rate (%)"
                            chart_df = display_df.rename(
                                columns={
                                    "team_win_rate": "value"
                                }
                            )

                        st.markdown(
                            f"### {chart_title}"
                        )

                        fig = px.bar(
                            chart_df.sort_values(
                                "value",
                                ascending=True
                            ),
                            x="value",
                            y="player_name",
                            orientation="h",
                            labels={
                                "value": y_title,
                                "player_name": "Player",
                            },
                            text="value",
                        )

                        fig.update_traces(
                            texttemplate=(
                                "%{text:.1f}"
                                if active_view in {
                                    "average",
                                    "win_rate",
                                }
                                else "%{text:.0f}"
                            ),
                            textposition="outside"
                        )

                        fig.update_layout(
                            height=560,
                            margin=dict(
                                l=20,
                                r=30,
                                t=30,
                                b=30
                            ),
                            yaxis={
                                "categoryorder": "total ascending"
                            },
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                        st.divider()

                        st.markdown("### 🥇 Close Match Podium")

                        podium = display_df.head(3)

                        medals = ["🥇", "🥈", "🥉"]
                        labels = [
                            "CLOSE MATCH KING",
                            "ELITE WARRIOR",
                            "ELITE WARRIOR",
                        ]

                        podium_cols = st.columns(
                            len(podium)
                        )

                        for col, (_, player), medal, label in zip(
                            podium_cols,
                            podium.iterrows(),
                            medals,
                            labels
                        ):
                            player_name = html.escape(
                                str(player["player_name"])
                            )

                            average = float(
                                player["avg_runs_close_matches"]
                            )

                            matches = int(
                                player["close_matches_played"]
                            )

                            wins = int(
                                player["close_matches_team_won"]
                            )

                            win_rate = float(
                                player["team_win_rate"]
                            )

                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:22px;
                                        border:1px solid #d9d9d9;
                                        border-radius:18px;
                                        text-align:center;
                                        min-height:230px;
                                        box-sizing:border-box;
                                    ">
                                        <div style="
                                            font-size:38px;
                                        ">
                                            {medal}
                                        </div>

                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:0.65;
                                            margin-top:4px;
                                        ">
                                            {label}
                                        </div>

                                        <div style="
                                            font-size:19px;
                                            font-weight:700;
                                            margin:9px 0;
                                        ">
                                            {player_name}
                                        </div>

                                        <div style="
                                            font-size:26px;
                                            font-weight:800;
                                        ">
                                            {average:.2f}
                                        </div>

                                        <div style="
                                            font-size:12px;
                                            opacity:0.7;
                                        ">
                                            average runs
                                        </div>

                                        <div style="
                                            margin-top:12px;
                                            font-size:12px;
                                        ">
                                            ⚔️ {matches} matches
                                            &nbsp; • &nbsp;
                                            🏆 {wins} wins
                                        </div>

                                        <div style="
                                            margin-top:7px;
                                            font-size:12px;
                                            opacity:0.75;
                                        ">
                                            📈 {win_rate:.1f}% team win rate
                                        </div>
                                    </div>
                                    """
                                )

                        st.divider()

                        st.markdown("### ⚔️ Close Match Battle Board")

                        st.caption(
                            "Run Power is relative to the top average-run "
                            "performer. It is a visual ranking aid, not an "
                            "official cricket statistic."
                        )

                        leaderboard = (
                            df.sort_values(
                                "avg_runs_close_matches",
                                ascending=False
                            )
                            .head(20)
                            .copy()
                        )

                        max_average = max(
                            float(
                                leaderboard[
                                    "avg_runs_close_matches"
                                ].max()
                            ),
                            1
                        )

                        for rank, (_, player) in enumerate(
                            leaderboard.iterrows(),
                            start=1
                        ):
                            player_name = html.escape(
                                str(player["player_name"])
                            )

                            average = float(
                                player["avg_runs_close_matches"]
                            )

                            matches = int(
                                player["close_matches_played"]
                            )

                            wins = int(
                                player["close_matches_team_won"]
                            )

                            win_rate = float(
                                player["team_win_rate"]
                            )

                            power = min(
                                average / max_average * 100,
                                100
                            )

                            if rank == 1:
                                rank_icon = "👑"
                                badge = "CLOSE MATCH KING"
                            elif rank <= 3:
                                rank_icon = "🥇"
                                badge = "ELITE"
                            elif rank <= 5:
                                rank_icon = "🔥"
                                badge = "TOP 5"
                            else:
                                rank_icon = "⚡"
                                badge = "WARRIOR"

                            st.html(
                                f"""
                                <div style="
                                    padding:14px 18px;
                                    border:1px solid
                                        rgba(255,255,255,0.10);
                                    border-radius:14px;
                                    margin:7px 0;
                                    background:
                                        rgba(255,255,255,0.025);
                                ">
                                    <div style="
                                        display:flex;
                                        align-items:center;
                                        gap:14px;
                                    ">
                                        <div style="
                                            width:38px;
                                            text-align:center;
                                            font-size:22px;
                                        ">
                                            {rank_icon}
                                        </div>

                                        <div style="
                                            min-width:175px;
                                        ">
                                            <div style="
                                                font-size:15px;
                                                font-weight:700;
                                            ">
                                                #{rank} {player_name}
                                            </div>

                                            <div style="
                                                font-size:10px;
                                                letter-spacing:1px;
                                                opacity:0.55;
                                                margin-top:3px;
                                            ">
                                                {badge}
                                            </div>
                                        </div>

                                        <div style="
                                            flex:1;
                                            min-width:120px;
                                        ">
                                            <div style="
                                                display:flex;
                                                justify-content:
                                                    space-between;
                                                font-size:11px;
                                                margin-bottom:5px;
                                            ">
                                                <span>RUN POWER</span>
                                                <span>{power:.1f}%</span>
                                            </div>

                                            <div style="
                                                height:8px;
                                                border-radius:8px;
                                                background:
                                                    rgba(
                                                        255,255,255,0.08
                                                    );
                                                overflow:hidden;
                                            ">
                                                <div style="
                                                    width:{power:.1f}%;
                                                    height:100%;
                                                    border-radius:8px;
                                                    background:
                                                        linear-gradient(
                                                            90deg,
                                                            #ffd700,
                                                            #ff9f1c
                                                        );
                                                "></div>
                                            </div>
                                        </div>

                                        <div style="
                                            min-width:80px;
                                            text-align:right;
                                        ">
                                            <div style="
                                                font-size:18px;
                                                font-weight:800;
                                            ">
                                                {average:.2f}
                                            </div>
                                            <div style="
                                                font-size:10px;
                                                opacity:0.55;
                                            ">
                                                AVG RUNS
                                            </div>
                                        </div>

                                        <div style="
                                            min-width:145px;
                                            text-align:right;
                                            font-size:12px;
                                            opacity:0.8;
                                        ">
                                            ⚔️ {matches}
                                            &nbsp; • &nbsp;
                                            🏆 {wins}
                                            &nbsp; • &nbsp;
                                            📈 {win_rate:.1f}%
                                        </div>
                                    </div>
                                </div>
                                """
                            )

                        st.divider()

                        st.markdown("### 🔎 Player Explorer")

                        player_options = df[
                            "player_name"
                        ].astype(str).tolist()

                        selected_player = st.selectbox(
                            "Choose a player",
                            player_options,
                            key="q15_player_explorer"
                        )

                        player_row = df[
                            df["player_name"].astype(str)
                            == selected_player
                        ].iloc[0]

                        exp_col1, exp_col2, exp_col3, exp_col4 = (
                            st.columns(4)
                        )

                        with exp_col1:
                            st.metric(
                                "🔥 Average Runs",
                                f"{float(player_row['avg_runs_close_matches']):.2f}"
                            )

                        with exp_col2:
                            st.metric(
                                "⚔️ Close Matches",
                                int(player_row["close_matches_played"])
                            )

                        with exp_col3:
                            st.metric(
                                "🏆 Team Wins",
                                int(player_row["close_matches_team_won"])
                            )

                        with exp_col4:
                            st.metric(
                                "📈 Win Rate",
                                f"{float(player_row['team_win_rate']):.1f}%"
                            )

                        st.divider()

                        st.markdown("### 📊 Runs vs Team Win Rate")

                        scatter_df = df[
                            [
                                "player_name",
                                "avg_runs_close_matches",
                                "team_win_rate",
                                "close_matches_played",
                            ]
                        ].copy()

                        scatter_fig = px.scatter(
                            scatter_df,
                            x="avg_runs_close_matches",
                            y="team_win_rate",
                            size="close_matches_played",
                            hover_name="player_name",
                            labels={
                                "avg_runs_close_matches":
                                    "Average Runs in Close Matches",
                                "team_win_rate":
                                    "Team Win Rate When Batting",
                                "close_matches_played":
                                    "Close Matches Played",
                            },
                        )

                        scatter_fig.update_layout(
                            height=500,
                            margin=dict(
                                l=20,
                                r=20,
                                t=30,
                                b=30
                            ),
                        )

                        st.plotly_chart(
                            scatter_fig,
                            use_container_width=True
                        )

                        st.divider()

                        st.markdown("### 📋 Complete Close Match Stats")

                        table_df = df[
                            [
                                "player_name",
                                "avg_runs_close_matches",
                                "close_matches_played",
                                "close_matches_team_won",
                                "team_win_rate",
                            ]
                        ].copy()

                        table_df.insert(
                            0,
                            "Rank",
                            range(1, len(table_df) + 1)
                        )

                        table_df["avg_runs_close_matches"] = (
                            table_df[
                                "avg_runs_close_matches"
                            ].round(2)
                        )

                        table_df["team_win_rate"] = (
                            table_df["team_win_rate"].round(1)
                        )

                        table_df.columns = [
                            "Rank",
                            "Player",
                            "Average Runs",
                            "Close Matches",
                            "Team Wins",
                            "Team Win Rate %",
                        ]

                        st.dataframe(
                            table_df,
                            use_container_width=True,
                            hide_index=True,
                            height=600
                        )

                        st.download_button(
                            "Download Q15 results as CSV",
                            df.to_csv(index=False),
                            file_name="Q15_close_match_performance.csv",
                            mime="text/csv"
                        )


            elif choice.startswith("Q16:"):

                st.subheader("🏆 Batting Trend Arena")
                st.caption(
                    "Track how batting performance changes year by year • "
                    "2020–2026 • Avg Runs / Avg Strike Rate"
                )

                df = df.copy()
                df["year"] = df["year"].astype(str)
                df["avg_runs"] = pd.to_numeric(df["avg_runs"], errors="coerce")
                df["avg_strike_rate"] = pd.to_numeric(
                    df["avg_strike_rate"], errors="coerce"
                )
                df = df.dropna(
                    subset=["player_name", "year", "avg_runs", "avg_strike_rate"]
                )

                years = [str(y) for y in range(2020, 2027)]

                summary = (
                    df.pivot_table(
                        index="player_name",
                        columns="year",
                        values="avg_runs",
                        aggfunc="mean"
                    )
                    .reindex(columns=years)
                )

                sr_summary = (
                    df.pivot_table(
                        index="player_name",
                        columns="year",
                        values="avg_strike_rate",
                        aggfunc="mean"
                    )
                    .reindex(columns=years)
                )

                stats = pd.DataFrame(index=summary.index)
                stats["avg_runs"] = summary.mean(axis=1)
                stats["avg_sr"] = sr_summary.mean(axis=1)
                stats["runs_2020"] = summary["2020"]
                stats["runs_2026"] = summary["2026"]
                stats["sr_2026"] = sr_summary["2026"]
                stats["run_growth"] = stats["runs_2026"] - stats["runs_2020"]
                stats["years_played"] = summary.notna().sum(axis=1)

                trends = (
                    df.groupby("player_name", sort=False)["trend"]
                    .first()
                )
                stats["trend"] = trends.reindex(stats.index).fillna("→ Stable")
                stats = stats.reset_index()

                if stats.empty:
                    st.info("No Q16 batting trend data is available.")
                else:
                    improving = int((stats["trend"] == "↗ Improving").sum())
                    declining = int((stats["trend"] == "↘ Declining").sum())
                    stable = int((stats["trend"] == "→ Stable").sum())

                    champion = stats.sort_values(
                        ["run_growth", "runs_2026"],
                        ascending=False
                    ).iloc[0]

                    st.html(
                        f"""
                        <div style="
                            padding:28px;
                            border-radius:20px;
                            border:1px solid rgba(255,215,0,0.35);
                            text-align:center;
                            margin:5px 0 20px 0;
                            background:linear-gradient(
                                135deg,
                                rgba(255,215,0,0.16),
                                rgba(255,255,255,0.035)
                            );
                        ">
                            <div style="font-size:48px;">👑</div>
                            <div style="
                                font-size:12px;
                                letter-spacing:3px;
                                opacity:0.7;
                                margin-top:8px;
                            ">GROWTH KING</div>
                            <div style="
                                font-size:30px;
                                font-weight:800;
                                margin:8px 0;
                            ">{html.escape(str(champion["player_name"]))}</div>
                            <div style="
                                font-size:22px;
                                font-weight:700;
                            ">
                                {champion["run_growth"]:+.2f} avg runs
                            </div>
                            <div style="
                                font-size:13px;
                                opacity:0.7;
                                margin-top:6px;
                            ">
                                2020 → 2026 batting growth
                            </div>
                        </div>
                        """
                    )

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("👥 Players", len(stats))
                    with c2:
                        st.metric("↗ Improving", improving)
                    with c3:
                        st.metric("→ Stable", stable)
                    with c4:
                        st.metric("↘ Declining", declining)

                    st.divider()

                    st.markdown("### 🥇 Growth Podium")

                    podium = stats.sort_values(
                        ["run_growth", "runs_2026"],
                        ascending=False
                    ).head(3)
                    medals = ["🥇", "🥈", "🥉"]
                    labels = ["GROWTH KING", "RUNNER-UP", "BRONZE"]

                    cols = st.columns(len(podium))

                    for col, (_, player), medal, label in zip(
                        cols, podium.iterrows(), medals, labels
                    ):
                        with col:
                            st.html(
                                f"""
                                <div style="
                                    padding:20px;
                                    border:1px solid #d9d9d9;
                                    border-radius:16px;
                                    text-align:center;
                                    min-height:185px;
                                ">
                                    <div style="font-size:34px;">{medal}</div>
                                    <div style="
                                        font-size:10px;
                                        letter-spacing:2px;
                                        opacity:0.65;
                                    ">{label}</div>
                                    <div style="
                                        font-size:18px;
                                        font-weight:700;
                                        margin:9px 0;
                                    ">
                                        {html.escape(str(player["player_name"]))}
                                    </div>
                                    <div style="
                                        font-size:25px;
                                        font-weight:800;
                                    ">
                                        {player["run_growth"]:+.2f}
                                    </div>
                                    <div style="
                                        font-size:11px;
                                        opacity:0.65;
                                    ">
                                        avg-run change
                                    </div>
                                </div>
                                """
                            )

                    st.divider()

                    st.markdown("### 🎮 Performance Battle")

                    metric = st.radio(
                        "Choose a battle metric",
                        [
                            "📈 Avg Runs",
                            "⚡ Strike Rate",
                            "🚀 Run Growth",
                            "🎯 Trend"
                        ],
                        horizontal=True,
                        key="q16_metric"
                    )

                    chart_df = df.copy()

                    if metric == "📈 Avg Runs":
                        top_players = (
                            stats.sort_values("runs_2026", ascending=False)
                            .head(10)["player_name"]
                            .tolist()
                        )
                        chart_df = chart_df[
                            chart_df["player_name"].isin(top_players)
                        ]
                        chart_df = chart_df.sort_values("year")
                        fig = px.line(
                            chart_df,
                            x="year",
                            y="avg_runs",
                            color="player_name",
                            markers=True,
                            title="Top 10 Players by 2026 Average Runs"
                        )
                        fig.update_layout(
                            xaxis_title="Year",
                            yaxis_title="Average Runs",
                            legend_title="Player"
                        )

                    elif metric == "⚡ Strike Rate":
                        top_players = (
                            stats.sort_values("sr_2026", ascending=False)
                            .head(10)["player_name"]
                            .tolist()
                        )
                        chart_df = chart_df[
                            chart_df["player_name"].isin(top_players)
                        ]
                        chart_df = chart_df.sort_values("year")
                        fig = px.line(
                            chart_df,
                            x="year",
                            y="avg_strike_rate",
                            color="player_name",
                            markers=True,
                            title="Top 10 Players by 2026 Strike Rate"
                        )
                        fig.update_layout(
                            xaxis_title="Year",
                            yaxis_title="Average Strike Rate",
                            legend_title="Player"
                        )

                    elif metric == "🚀 Run Growth":
                        growth_df = (
                            stats.sort_values(
                                ["run_growth", "runs_2026"],
                                ascending=False
                            )
                            .head(15)
                            .sort_values("run_growth")
                        )
                        fig = px.bar(
                            growth_df,
                            x="run_growth",
                            y="player_name",
                            orientation="h",
                            text="run_growth",
                            title="Biggest 2020 → 2026 Run Growth"
                        )
                        fig.update_layout(
                            xaxis_title="Change in Average Runs",
                            yaxis_title="Player"
                        )

                    else:
                        trend_df = (
                            stats["trend"]
                            .value_counts()
                            .rename_axis("trend")
                            .reset_index(name="players")
                        )
                        fig = px.bar(
                            trend_df,
                            x="trend",
                            y="players",
                            text="players",
                            title="Batting Trend Distribution"
                        )
                        fig.update_layout(
                            xaxis_title="Trend",
                            yaxis_title="Players"
                        )

                    fig.update_layout(
                        height=480,
                        hovermode="x unified"
                    )
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        key="q16_battle_chart"
                    )

                    st.divider()

                    st.markdown("### ⚔️ Player Explorer")

                    player_options = sorted(
                        stats["player_name"].astype(str).unique().tolist()
                    )
                    selected_player = st.selectbox(
                        "Choose a player",
                        player_options,
                        key="q16_player"
                    )

                    player_df = (
                        df[df["player_name"].astype(str) == selected_player]
                        .sort_values("year")
                    )

                    pc1, pc2, pc3 = st.columns(3)
                    player_stats = stats[
                        stats["player_name"].astype(str) == selected_player
                    ].iloc[0]

                    with pc1:
                        st.metric(
                            "2026 Avg Runs",
                            f"{player_stats['runs_2026']:.2f}"
                        )
                    with pc2:
                        st.metric(
                            "2026 Strike Rate",
                            f"{player_stats['sr_2026']:.2f}"
                        )
                    with pc3:
                        st.metric(
                            "2020 → 2026",
                            f"{player_stats['run_growth']:+.2f}"
                        )

                    explorer_metric = st.radio(
                        "Explore",
                        ["Average Runs", "Strike Rate"],
                        horizontal=True,
                        key="q16_explorer_metric"
                    )

                    y_col = (
                        "avg_runs"
                        if explorer_metric == "Average Runs"
                        else "avg_strike_rate"
                    )

                    fig = px.line(
                        player_df,
                        x="year",
                        y=y_col,
                        markers=True,
                        title=f"{selected_player} • {explorer_metric} by Year"
                    )
                    fig.update_layout(
                        height=400,
                        xaxis_title="Year",
                        yaxis_title=explorer_metric
                    )
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        key="q16_player_chart"
                    )

                    st.divider()

                    st.markdown("### 🏆 Trend Leaderboard")

                    board = (
                        stats.sort_values(
                            ["run_growth", "runs_2026"],
                            ascending=False
                        )
                        .head(20)
                        .copy()
                    )

                    board.insert(0, "Rank", range(1, len(board) + 1))
                    board["Growth"] = board["run_growth"].map(
                        lambda x: f"{x:+.2f}"
                    )
                    board["2026 Runs"] = board["runs_2026"].map(
                        lambda x: f"{x:.2f}"
                    )
                    board["2026 SR"] = board["sr_2026"].map(
                        lambda x: f"{x:.2f}"
                    )

                    board = board[
                        [
                            "Rank",
                            "player_name",
                            "2026 Runs",
                            "2026 SR",
                            "Growth",
                            "trend"
                        ]
                    ].copy()

                    board.columns = [
                        "Rank",
                        "Player",
                        "2026 Avg Runs",
                        "2026 Avg SR",
                        "2020 → 2026",
                        "Trend"
                    ]

                    st.dataframe(
                        board,
                        use_container_width=True,
                        hide_index=True,
                        height=520
                    )

                    st.download_button(
                        "Download Q16 results as CSV",
                        df.to_csv(index=False),
                        file_name="Q16_yearly_batting_trend.csv",
                        mime="text/csv"
                    )
            elif choice.startswith("Q17:"):

                st.subheader("🏏 Toss Advantage Arena")
                st.caption(
                    "Does winning the toss actually give teams an advantage?"
                )

                df = df.copy()
                df["toss_decision"] = (
                    df["toss_decision"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )
                df["Decision"] = df["toss_decision"].map(
                    {"bat": "🏏 BAT FIRST", "bowl": "⚾ BOWL FIRST"}
                )
                df["Win Rate"] = pd.to_numeric(
                    df["win_pct_after_winning_toss"],
                    errors="coerce"
                )
                df = df.dropna(subset=["Decision", "Win Rate"])

                bat_pct = float(
                    df.loc[df["toss_decision"] == "bat", "Win Rate"].iloc[0]
                ) if not df.loc[df["toss_decision"] == "bat"].empty else 0

                bowl_pct = float(
                    df.loc[df["toss_decision"] == "bowl", "Win Rate"].iloc[0]
                ) if not df.loc[df["toss_decision"] == "bowl"].empty else 0

                gap = bowl_pct - bat_pct

                if bowl_pct > bat_pct:
                    champion = "⚾ BOWL FIRST"
                    champion_pct = bowl_pct
                    champion_icon = "👑"
                elif bat_pct > bowl_pct:
                    champion = "🏏 BAT FIRST"
                    champion_pct = bat_pct
                    champion_icon = "👑"
                else:
                    champion = "⚖️ TIE"
                    champion_pct = bat_pct
                    champion_icon = "⚖️"

                st.html(
                    f"""
                    <div style="
                        padding:28px;
                        border-radius:20px;
                        border:1px solid rgba(255,215,0,0.30);
                        text-align:center;
                        margin:5px 0 22px 0;
                        background:linear-gradient(
                            135deg,
                            rgba(255,215,0,0.14),
                            rgba(255,255,255,0.03)
                        );
                    ">
                        <div style="font-size:46px">{champion_icon}</div>
                        <div style="
                            font-size:12px;
                            letter-spacing:3px;
                            opacity:0.65;
                            margin-top:8px;
                        ">
                            TOSS CHAMPION
                        </div>
                        <div style="
                            font-size:31px;
                            font-weight:800;
                            margin:8px 0;
                        ">
                            {champion}
                        </div>
                        <div style="
                            font-size:23px;
                            font-weight:700;
                        ">
                            {champion_pct:.2f}% WIN RATE
                        </div>
                    </div>
                    """
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("🏏 Bat First", f"{bat_pct:.2f}%")

                with col2:
                    st.metric("⚾ Bowl First", f"{bowl_pct:.2f}%")

                with col3:
                    st.metric(
                        "⚡ Decision Gap",
                        f"{abs(gap):.2f} pts",
                        delta=(
                            "Bowl first"
                            if gap > 0
                            else "Bat first"
                            if gap < 0
                            else "Tie"
                        )
                    )

                st.divider()

                st.markdown("### 🎮 Choose Your Toss Strategy")

                strategy = st.radio(
                    "Explore",
                    ["🏏 BAT FIRST", "⚾ BOWL FIRST", "⚔️ HEAD-TO-HEAD"],
                    horizontal=True,
                    key="q17_strategy"
                )

                if strategy == "🏏 BAT FIRST":
                    selected_pct = bat_pct
                    label = "BAT FIRST"
                    icon = "🏏"
                    colour_text = (
                        "🔥 Above the 50% benchmark"
                        if bat_pct >= 50
                        else "⚠️ Below the 50% benchmark"
                    )
                    st.progress(min(max(bat_pct / 100, 0), 1))
                    st.info(
                        f"{icon} Toss-winning teams choosing to bat first "
                        f"won {bat_pct:.2f}% of these matches. {colour_text}."
                    )

                elif strategy == "⚾ BOWL FIRST":
                    selected_pct = bowl_pct
                    label = "BOWL FIRST"
                    icon = "⚾"
                    colour_text = (
                        "🔥 Above the 50% benchmark"
                        if bowl_pct >= 50
                        else "⚠️ Below the 50% benchmark"
                    )
                    st.progress(min(max(bowl_pct / 100, 0), 1))
                    st.info(
                        f"{icon} Toss-winning teams choosing to bowl first "
                        f"won {bowl_pct:.2f}% of these matches. {colour_text}."
                    )

                else:
                    selected_pct = None
                    label = "HEAD-TO-HEAD"
                    if gap > 0:
                        st.success(
                            f"⚾ **BOWL FIRST WINS** — a {abs(gap):.2f} "
                            f"percentage-point advantage over batting first."
                        )
                    elif gap < 0:
                        st.success(
                            f"🏏 **BAT FIRST WINS** — a {abs(gap):.2f} "
                            f"percentage-point advantage over bowling first."
                        )
                    else:
                        st.info("⚖️ Both toss decisions have the same win rate.")

                st.divider()

                st.markdown("### 📊 Toss Battle Chart")

                chart_df = df[["Decision", "Win Rate"]].copy()
                chart_df = chart_df.sort_values("Win Rate", ascending=False)

                fig = px.bar(
                    chart_df,
                    x="Decision",
                    y="Win Rate",
                    text="Win Rate",
                    title="Win Rate After Winning the Toss",
                    labels={"Win Rate": "Win Rate (%)", "Decision": "Toss Decision"},
                    hover_data={"Win Rate": ":.2f"}
                )
                fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
                fig.update_yaxes(range=[0, max(100, chart_df["Win Rate"].max() + 10)])
                fig.add_hline(
                    y=50,
                    line_dash="dash",
                    annotation_text="50% benchmark"
                )
                fig.update_layout(
                    height=430,
                    margin=dict(l=20, r=20, t=65, b=20)
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="q17_win_rate_chart"
                )

                st.markdown("### 🗺️ Interactive Toss Advantage Map")

                map_df = pd.DataFrame(
                    {
                        "Decision": ["🏏 BAT FIRST", "⚾ BOWL FIRST"],
                        "Win Rate": [bat_pct, bowl_pct]
                    }
                )
                map_df["Distance from 50%"] = (
                    map_df["Win Rate"] - 50
                ).round(2)

                heatmap = px.imshow(
                    map_df.set_index("Decision")[["Win Rate"]],
                    text_auto=".2f",
                    aspect="auto",
                    title="Toss Decision → Match-Winning Probability",
                    labels={"x": "", "y": "", "color": "Win Rate (%)"}
                )
                heatmap.update_layout(
                    height=280,
                    margin=dict(l=20, r=20, t=65, b=20)
                )
                st.plotly_chart(
                    heatmap,
                    use_container_width=True,
                    key="q17_advantage_map"
                )

                st.caption(
                    "The map is a decision heatmap: darker/higher cells indicate "
                    "a stronger match-winning rate for the toss-winning team."
                )

                st.divider()

                st.markdown("### 🏆 Toss Decision Scorecards")

                card1, card2 = st.columns(2)

                with card1:
                    st.html(
                        f"""
                        <div style="
                            padding:22px;
                            border:1px solid rgba(255,255,255,0.10);
                            border-radius:16px;
                            min-height:165px;
                        ">
                            <div style="font-size:30px">🏏</div>
                            <div style="
                                font-size:12px;
                                letter-spacing:2px;
                                opacity:0.6;
                                margin-top:5px;
                            ">
                                BAT FIRST
                            </div>
                            <div style="
                                font-size:28px;
                                font-weight:800;
                                margin:7px 0;
                            ">
                                {bat_pct:.2f}%
                            </div>
                            <div style="opacity:0.7">
                                {"🔥 Above" if bat_pct >= 50 else "⚠️ Below"} the 50% benchmark
                            </div>
                        </div>
                        """
                    )

                with card2:
                    st.html(
                        f"""
                        <div style="
                            padding:22px;
                            border:1px solid rgba(255,255,255,0.10);
                            border-radius:16px;
                            min-height:165px;
                        ">
                            <div style="font-size:30px">⚾</div>
                            <div style="
                                font-size:12px;
                                letter-spacing:2px;
                                opacity:0.6;
                                margin-top:5px;
                            ">
                                BOWL FIRST
                            </div>
                            <div style="
                                font-size:28px;
                                font-weight:800;
                                margin:7px 0;
                            ">
                                {bowl_pct:.2f}%
                            </div>
                            <div style="opacity:0.7">
                                {"🔥 Above" if bowl_pct >= 50 else "⚠️ Below"} the 50% benchmark
                            </div>
                        </div>
                        """
                    )

                st.divider()

                if gap > 0:
                    st.success(
                        f"⚾ **BOWL FIRST WINS!** Toss-winning teams that "
                        f"bowled first had a **{gap:.2f} percentage-point** "
                        f"higher win rate."
                    )
                elif gap < 0:
                    st.success(
                        f"🏏 **BAT FIRST WINS!** Toss-winning teams that "
                        f"batted first had a **{abs(gap):.2f} percentage-point** "
                        f"higher win rate."
                    )
                else:
                    st.info(
                        "⚖️ Both toss decisions produced the same win rate."
                    )

                st.caption(
                    "Win rate is calculated separately for matches where the "
                    "toss-winning team chose to bat or bowl."
                )

                st.download_button(
                    "📥 Download Q17 results as CSV",
                    df[["toss_decision", "Win Rate"]].to_csv(index=False),
                    file_name="Q17_toss_advantage.csv",
                    mime="text/csv"
                )


            elif choice.startswith("Q18:"):

                st.subheader(
                    "🎯 Economy Kings"
                )

                st.caption(
                    "Limited-overs bowling leaderboard • "
                    "10+ matches • 2+ overs per match"
                )

                df = df.copy()

                df["economy_rate"] = pd.to_numeric(
                    df["economy_rate"],
                    errors="coerce"
                )

                df["wickets_taken"] = pd.to_numeric(
                    df["wickets_taken"],
                    errors="coerce"
                )

                df = df.dropna(
                    subset=[
                        "economy_rate"
                    ]
                ).sort_values(
                    "economy_rate"
                ).reset_index(
                    drop=True
                )

                if df.empty:

                    st.warning(
                        "No qualifying bowlers found."
                    )

                else:

                    formats = [
                        "All"
                    ] + sorted(
                        df["format"]
                        .dropna()
                        .unique()
                        .tolist()
                    )

                    selected_format = st.radio(
                        "Format",
                        formats,
                        horizontal=True
                    )

                    display_df = (
                        df
                        if selected_format == "All"
                        else df[
                            df["format"]
                            == selected_format
                        ]
                    ).copy()

                    display_df = (
                        display_df
                        .reset_index(
                            drop=True
                        )
                    )

                    if display_df.empty:

                        st.info(
                            "No bowlers available for this format."
                        )

                    else:

                        leader = (
                            display_df.iloc[0]
                        )

                        st.html(
                            f"""
                            <div style="
                                padding:25px;
                                border-radius:15px;
                                border:1px solid #ddd;
                                background:linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.05)
                                );
                                text-align:center;
                                margin-bottom:20px;
                            ">

                                <div style="
                                    font-size:42px;
                                ">
                                    🏆
                                </div>

                                <div style="
                                    font-size:14px;
                                ">
                                    ECONOMY KING
                                </div>

                                <div style="
                                    font-size:30px;
                                    font-weight:700;
                                    margin:8px;
                                ">
                                    {leader['player_name']}
                                </div>

                                <div style="
                                    font-size:20px;
                                ">
                                    {leader['economy_rate']:.2f}
                                    Economy
                                </div>

                                <div style="
                                    margin-top:8px;
                                    opacity:0.75;
                                ">
                                    {leader['format']} •
                                    {int(
                                        leader['wickets_taken']
                                    )} wickets
                                </div>

                            </div>
                            """
                        )

                        st.markdown(
                            "### 🏅 Top 3"
                        )

                        top3 = display_df.head(3)

                        medals = [
                            "🥇",
                            "🥈",
                            "🥉"
                        ]

                        cols = st.columns(
                            len(top3)
                        )

                        for col, (_, row), medal in zip(
                            cols,
                            top3.iterrows(),
                            medals
                        ):

                            with col:

                                st.html(
                                    f"""
                                    <div style="
                                        padding:18px;
                                        border:1px solid #ddd;
                                        border-radius:12px;
                                        text-align:center;
                                        min-height:150px;
                                    ">

                                        <div style="
                                            font-size:30px;
                                        ">
                                            {medal}
                                        </div>

                                        <div style="
                                            font-size:17px;
                                            font-weight:600;
                                        ">
                                            {row['player_name']}
                                        </div>

                                        <div style="
                                            font-size:25px;
                                            font-weight:700;
                                            margin:8px;
                                        ">
                                            {row['economy_rate']:.2f}
                                        </div>

                                        <div style="
                                            opacity:0.7;
                                        ">
                                            {row['format']} •
                                            {int(
                                                row['wickets_taken']
                                            )} wickets
                                        </div>

                                    </div>
                                    """
                                )

                        st.divider()

                        col1, col2, col3 = st.columns(3)

                        with col1:

                            st.metric(
                                "🎯 Best Economy",
                                f"{leader['economy_rate']:.2f}"
                            )

                        with col2:

                            st.metric(
                                "🔥 Leader Wickets",
                                int(
                                    leader[
                                        "wickets_taken"
                                    ]
                                )
                            )

                        with col3:

                            st.metric(
                                "🏏 Qualified Bowlers",
                                len(display_df)
                            )

                        st.divider()

                        st.markdown(
                            "### ⚔️ Economy Battle"
                        )

                        battle = (
                            display_df
                            .head(10)
                            .copy()
                        )

                        max_economy = max(
                            battle[
                                "economy_rate"
                            ].max(),
                            1
                        )

                        for rank, (_, row) in enumerate(
                            battle.iterrows(),
                            start=1
                        ):

                            pct = (
                                row["economy_rate"]
                                / max_economy
                            )

                            st.markdown(
                                f"**{rank}. "
                                f"{row['player_name']}** "
                                f"— "
                                f"{row['economy_rate']:.2f}"
                            )

                            st.progress(
                                min(
                                    max(
                                        pct,
                                        0
                                    ),
                                    1
                                )
                            )

                        st.divider()

                        st.markdown(
                            "### 🏏 Bowling Leaderboard"
                        )

                        leaderboard = (
                            display_df.copy()
                        )

                        leaderboard.insert(
                            0,
                            "Rank",
                            range(
                                1,
                                len(leaderboard) + 1
                            )
                        )

                        leaderboard["Economy"] = (
                            leaderboard[
                                "economy_rate"
                            ].map(
                                lambda x:
                                f"{x:.2f}"
                            )
                        )

                        leaderboard["Wickets"] = (
                            leaderboard[
                                "wickets_taken"
                            ].astype(int)
                        )

                        leaderboard = leaderboard[
                            [
                                "Rank",
                                "player_name",
                                "Economy",
                                "Wickets",
                                "format"
                            ]
                        ]

                        leaderboard.columns = [
                            "Rank",
                            "Bowler",
                            "Economy",
                            "Wickets",
                            "Format"
                        ]

                        st.dataframe(
                            leaderboard,
                            use_container_width=True,
                            hide_index=True
                        )

                        st.success(
                            f"🎯 **{leader['player_name']} leads "
                            f"the {selected_format} leaderboard "
                            f"with a "
                            f"{leader['economy_rate']:.2f} "
                            f"economy rate.**"
                        )

                        st.download_button(
                            "Download results as CSV",
                            display_df.to_csv(
                                index=False
                            ),
                            file_name="Q18.csv"
                        )



            elif choice.startswith("Q19:"):

                st.subheader("🎯 Consistency Kings")
                st.caption(
                    "Batsmen since 2022 • 10+ balls per qualifying innings • "
                    "minimum 5 qualifying innings"
                )

                if "q19_view" not in st.session_state:
                    st.session_state["q19_view"] = "🏏 Most Runs"

                st.markdown("### 🎮 Choose Your Battle")
                button_cols = st.columns(3)
                q19_buttons = [
                    ("🏏 Most Runs", "q19_btn_runs"),
                    ("🎯 Consistency", "q19_btn_consistency"),
                    ("⚔️ Run vs Consistency", "q19_btn_balance"),
                ]

                for col, (label, key) in zip(button_cols, q19_buttons):
                    with col:
                        if st.button(label, key=key, width="stretch"):
                            st.session_state["q19_view"] = label
                            st.rerun()

                st.markdown(
                    """
                    <style>
                    div[data-testid="stButton"] > button {
                        min-height: 44px;
                        border-radius: 10px;
                        border: 1px solid rgba(255,255,255,0.20);
                        font-weight: 600;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )

                df = df.copy()
                for col in ["avg_runs", "stddev_runs"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                df = (
                    df.dropna(subset=["avg_runs", "stddev_runs"])
                    .sort_values(
                        ["stddev_runs", "avg_runs"],
                        ascending=[True, False]
                    )
                    .reset_index(drop=True)
                )

                if df.empty:
                    st.info("No qualifying batsmen found.")
                else:
                    consistent = df.iloc[0]
                    highest_avg = df.loc[df["avg_runs"].idxmax()]
                    df["consistency_score"] = 100 / (1 + df["stddev_runs"])
                    df["balance_score"] = df["avg_runs"] / (1 + df["stddev_runs"])
                    balanced = df.loc[df["balance_score"].idxmax()]
                    view = st.session_state["q19_view"]

                    if view == "🏏 Most Runs":
                        crown = highest_avg
                        crown_title = "RUN KING"
                        crown_detail = (
                            f"Standard deviation: {float(crown['stddev_runs']):.2f}"
                        )
                    elif view == "🎯 Consistency":
                        crown = consistent
                        crown_title = "RUN CONSISTENCY KING"
                        crown_detail = (
                            f"Standard deviation: {float(crown['stddev_runs']):.2f}"
                        )
                    else:
                        crown = balanced
                        crown_title = "RUN VS CONSISTENCY KING"
                        crown_detail = (
                            f"Standard deviation: {float(crown['stddev_runs']):.2f}"
                            f" • Balance score: {float(crown['balance_score']):.2f}"
                        )

                    st.html(
                        f'''
                        <div style="padding:28px;border-radius:20px;border:1px solid rgba(255,215,0,.35);
                             text-align:center;margin:5px 0 20px 0;
                             background:linear-gradient(135deg,rgba(255,215,0,.16),rgba(255,255,255,.035));">
                            <div style="font-size:46px;">👑</div>
                            <div style="font-size:12px;letter-spacing:3px;opacity:.7;">{crown_title}</div>
                            <div style="font-size:30px;font-weight:800;margin:8px 0;">{html.escape(str(crown["player_name"]))}</div>
                            <div style="font-size:23px;font-weight:700;">{float(crown["avg_runs"]):.2f} avg runs</div>
                            <div style="font-size:13px;opacity:.7;margin-top:5px;">{crown_detail}</div>
                        </div>
                        '''
                    )

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("🏏 Highest Avg", f"{highest_avg['avg_runs']:.2f}")
                    with c2:
                        st.metric("🎯 Most Consistent", str(consistent["player_name"]))
                    with c3:
                        st.metric("📉 Lowest Std Dev", f"{consistent['stddev_runs']:.2f}")
                    with c4:
                        st.metric("👥 Qualifying Players", len(df))

                    st.divider()

                    if view == "🏏 Most Runs":
                        chart_df = df.sort_values("avg_runs", ascending=False).head(15)
                        fig = px.bar(
                            chart_df.sort_values("avg_runs"),
                            x="avg_runs", y="player_name", orientation="h",
                            title="🏏 Top Batsmen by Average Runs",
                            labels={"avg_runs": "Average Runs", "player_name": "Player"},
                            hover_data={"stddev_runs": ":.2f"}
                        )
                    elif view == "🎯 Consistency":
                        chart_df = df.sort_values(
                            ["stddev_runs", "avg_runs"], ascending=[True, False]
                        ).head(15)
                        fig = px.bar(
                            chart_df.sort_values("stddev_runs", ascending=False),
                            x="stddev_runs", y="player_name", orientation="h",
                            title="🎯 Most Consistent Batsmen",
                            labels={"stddev_runs": "Standard Deviation", "player_name": "Player"},
                            hover_data={"avg_runs": ":.2f"}
                        )
                    else:
                        fig = px.scatter(
                            df, x="stddev_runs", y="avg_runs", text="player_name",
                            size="consistency_score",
                            title="⚔️ Average Runs vs Consistency",
                            labels={"stddev_runs": "Standard Deviation", "avg_runs": "Average Runs"},
                            hover_data={"consistency_score": ":.1f"}
                        )
                        fig.update_traces(textposition="top center")

                    fig.update_layout(
                        height=500,
                        margin=dict(l=20, r=20, t=60, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.divider()
                    st.markdown("### 🥇 Consistency Podium")
                    podium = df.head(3)
                    medals = ["🥇", "🥈", "🥉"]
                    cols = st.columns(len(podium))

                    for col, (_, row), medal in zip(cols, podium.iterrows(), medals):
                        with col:
                            st.html(
                                f'''
                                <div style="padding:18px;border:1px solid #d9d9d9;border-radius:14px;
                                     text-align:center;min-height:145px;">
                                    <div style="font-size:30px;">{medal}</div>
                                    <div style="font-weight:700;margin:6px 0;">{html.escape(str(row["player_name"]))}</div>
                                    <div style="font-size:24px;font-weight:800;">{float(row["stddev_runs"]):.2f}</div>
                                    <div style="opacity:.7;font-size:12px;">
                                        Std deviation • Avg {float(row["avg_runs"]):.2f}
                                    </div>
                                </div>
                                '''
                            )

                    st.divider()
                    st.markdown("### 🔎 Player Explorer")
                    selected_player = st.selectbox(
                        "Select a batsman",
                        df["player_name"].tolist(),
                        key="q19_player"
                    )
                    player = df.loc[df["player_name"] == selected_player].iloc[0]

                    e1, e2, e3 = st.columns(3)
                    with e1:
                        st.metric("🏏 Avg Runs", f"{player['avg_runs']:.2f}")
                    with e2:
                        st.metric("📉 Std Deviation", f"{player['stddev_runs']:.2f}")
                    with e3:
                        st.metric("🎯 Consistency Score", f"{player['consistency_score']:.1f}")

                    st.divider()
                    st.markdown("### ⚔️ Consistency Leaderboard")
                    board = df.copy()
                    board.insert(0, "Rank", range(1, len(board) + 1))
                    board["Avg Runs"] = board["avg_runs"].map(lambda x: f"{x:.2f}")
                    board["Std Dev"] = board["stddev_runs"].map(lambda x: f"{x:.2f}")
                    board = board[["Rank", "player_name", "Avg Runs", "Std Dev"]]
                    board.columns = ["Rank", "Player", "Avg Runs", "Std Dev"]

                    st.dataframe(
                        board,
                        use_container_width=True,
                        hide_index=True,
                        height=430
                    )

                    st.success(
                        f"🎯 **{consistent['player_name']} is the most consistent qualifying "
                        f"batsman with a standard deviation of {consistent['stddev_runs']:.2f}.**"
                    )

                    st.download_button(
                        "Download results as CSV",
                        df.drop(columns=["consistency_score", "balance_score"]).to_csv(index=False),
                        file_name="Q19_consistency.csv",
                        mime="text/csv"
                    )


            elif choice.startswith("Q20:"):

                st.subheader("🌍 Three-Format Titans")
                st.caption(
                    "Players active in Test, ODI and T20I • 20+ total matches • "
                    "Compare experience and batting averages across formats."
                )

                df = df.copy()

                numeric_cols = [
                    "test_matches", "odi_matches", "t20i_matches",
                    "test_avg", "odi_avg", "t20i_avg"
                ]

                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                required = [
                    "player_name", "test_matches", "odi_matches",
                    "t20i_matches", "test_avg", "odi_avg", "t20i_avg"
                ]

                missing = [c for c in required if c not in df.columns]

                if missing:
                    st.error(
                        "Q20 result is missing required columns: "
                        + ", ".join(missing)
                    )
                else:
                    df = df.dropna(subset=[
                        "player_name", "test_matches", "odi_matches",
                        "t20i_matches"
                    ]).copy()

                    df["total_matches"] = (
                        df["test_matches"]
                        + df["odi_matches"]
                        + df["t20i_matches"]
                    )

                    df["avg_overall"] = df[
                        ["test_avg", "odi_avg", "t20i_avg"]
                    ].mean(axis=1)

                    df["format_count"] = (
                        (df["test_matches"] > 0).astype(int)
                        + (df["odi_matches"] > 0).astype(int)
                        + (df["t20i_matches"] > 0).astype(int)
                    )

                    df = (
                        df[df["format_count"] == 3]
                        .sort_values(
                            ["total_matches", "avg_overall"],
                            ascending=[False, False]
                        )
                        .reset_index(drop=True)
                    )

                    if df.empty:
                        st.info("No three-format players meet the Q20 criteria.")
                    else:
                        experience_leader = df.iloc[0]

                        avg_cols = ["test_avg", "odi_avg", "t20i_avg"]
                        avg_labels = {
                            "test_avg": "Test",
                            "odi_avg": "ODI",
                            "t20i_avg": "T20I"
                        }

                        best_avg_col = max(
                            avg_cols,
                            key=lambda c: (
                                df[c].mean()
                                if df[c].notna().any()
                                else float("-inf")
                            )
                        )

                        total_matches = int(df["total_matches"].sum())
                        avg_total_matches = float(df["total_matches"].mean())

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:linear-gradient(
                                    135deg,
                                    rgba(255,215,0,0.18),
                                    rgba(255,255,255,0.035)
                                );
                            ">
                                <div style="font-size:50px;">👑</div>
                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:.7;
                                    margin-top:8px;
                                ">
                                    THREE-FORMAT TITAN
                                </div>
                                <div style="
                                    font-size:31px;
                                    font-weight:800;
                                    margin:8px 0;
                                ">
                                    {html.escape(str(experience_leader["player_name"]))}
                                </div>
                                <div style="font-size:24px;font-weight:800;">
                                    {int(experience_leader["total_matches"]):,} MATCHES
                                </div>
                                <div style="margin-top:7px;opacity:.7;font-size:13px;">
                                    Test {int(experience_leader["test_matches"]):,}
                                    &nbsp;•&nbsp;
                                    ODI {int(experience_leader["odi_matches"]):,}
                                    &nbsp;•&nbsp;
                                    T20I {int(experience_leader["t20i_matches"]):,}
                                </div>
                            </div>
                            """
                        )

                        c1, c2, c3, c4 = st.columns(4)

                        with c1:
                            st.metric("👥 Players", len(df))

                        with c2:
                            st.metric("🏏 Total Matches", f"{total_matches:,}")

                        with c3:
                            st.metric(
                                "📊 Avg Matches",
                                f"{avg_total_matches:.1f}"
                            )

                        with c4:
                            st.metric(
                                "⭐ Strongest Format",
                                avg_labels[best_avg_col]
                            )

                        st.divider()

                        st.markdown("### 🎮 Choose Your Battle")

                        mode = st.radio(
                            "Compare players by",
                            [
                                "🏏 Match Count",
                                "📊 Batting Average",
                                "⚔️ Format Balance",
                                "🔥 Total Experience"
                            ],
                            horizontal=True,
                            key="q20_mode"
                        )

                        if mode == "🏏 Match Count":
                            chart_df = df.melt(
                                id_vars="player_name",
                                value_vars=[
                                    "test_matches",
                                    "odi_matches",
                                    "t20i_matches"
                                ],
                                var_name="format",
                                value_name="matches"
                            )
                            chart_df["format"] = chart_df["format"].map({
                                "test_matches": "Test",
                                "odi_matches": "ODI",
                                "t20i_matches": "T20I"
                            })

                            fig = px.bar(
                                chart_df.head(15),
                                x="player_name",
                                y="matches",
                                color="format",
                                barmode="group",
                                title="🏏 Match Experience Battle — Top 15"
                            )
                            fig.update_layout(
                                height=500,
                                xaxis_title="Player",
                                yaxis_title="Matches"
                            )

                        elif mode == "📊 Batting Average":
                            chart_df = df.melt(
                                id_vars="player_name",
                                value_vars=[
                                    "test_avg",
                                    "odi_avg",
                                    "t20i_avg"
                                ],
                                var_name="format",
                                value_name="average"
                            )
                            chart_df["format"] = chart_df["format"].map({
                                "test_avg": "Test",
                                "odi_avg": "ODI",
                                "t20i_avg": "T20I"
                            })

                            fig = px.bar(
                                chart_df.head(15),
                                x="player_name",
                                y="average",
                                color="format",
                                barmode="group",
                                title="📊 Batting Average Battle — Top 15"
                            )
                            fig.update_layout(
                                height=500,
                                xaxis_title="Player",
                                yaxis_title="Batting Average"
                            )

                        elif mode == "⚔️ Format Balance":
                            chart_df = df.copy()
                            chart_df["Test %"] = (
                                chart_df["test_matches"]
                                / chart_df["total_matches"] * 100
                            )
                            chart_df["ODI %"] = (
                                chart_df["odi_matches"]
                                / chart_df["total_matches"] * 100
                            )
                            chart_df["T20I %"] = (
                                chart_df["t20i_matches"]
                                / chart_df["total_matches"] * 100
                            )

                            chart_df = chart_df.head(15).melt(
                                id_vars="player_name",
                                value_vars=["Test %", "ODI %", "T20I %"],
                                var_name="format",
                                value_name="share"
                            )

                            fig = px.bar(
                                chart_df,
                                x="player_name",
                                y="share",
                                color="format",
                                barmode="stack",
                                title="⚔️ Format Balance — Top 15"
                            )
                            fig.update_layout(
                                height=500,
                                xaxis_title="Player",
                                yaxis_title="Share of Matches (%)"
                            )

                        else:
                            chart_df = df.head(15).copy()

                            fig = px.bar(
                                chart_df,
                                x="player_name",
                                y="total_matches",
                                text="total_matches",
                                title="🔥 Total Career Experience — Top 15"
                            )
                            fig.update_traces(
                                textposition="outside"
                            )
                            fig.update_layout(
                                height=500,
                                xaxis_title="Player",
                                yaxis_title="Total Matches"
                            )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                        st.divider()

                        st.markdown("### 🥇 Three-Format Podium")

                        podium = df.head(3)
                        medals = ["🥇", "🥈", "🥉"]
                        labels = [
                            "FORMAT TITAN",
                            "ELITE ALL-ROUNDER",
                            "THREE-FORMAT STAR"
                        ]

                        cols = st.columns(len(podium))

                        for col, (_, player), medal, label in zip(
                            cols,
                            podium.iterrows(),
                            medals,
                            labels
                        ):
                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:20px;
                                        border:1px solid #d9d9d9;
                                        border-radius:18px;
                                        text-align:center;
                                        min-height:190px;
                                    ">
                                        <div style="font-size:36px;">
                                            {medal}
                                        </div>
                                        <div style="
                                            font-size:11px;
                                            letter-spacing:2px;
                                            opacity:.65;
                                        ">
                                            {label}
                                        </div>
                                        <div style="
                                            font-size:19px;
                                            font-weight:700;
                                            margin:9px 0;
                                        ">
                                            {html.escape(str(player["player_name"]))}
                                        </div>
                                        <div style="
                                            font-size:25px;
                                            font-weight:800;
                                        ">
                                            {int(player["total_matches"]):,}
                                        </div>
                                        <div style="font-size:12px;opacity:.7;">
                                            total matches
                                        </div>
                                        <div style="
                                            margin-top:9px;
                                            font-size:11px;
                                            opacity:.7;
                                        ">
                                            Test {int(player["test_matches"]):,}
                                            • ODI {int(player["odi_matches"]):,}
                                            • T20I {int(player["t20i_matches"]):,}
                                        </div>
                                    </div>
                                    """
                                )

                        st.divider()

                        st.markdown("### 🔎 Player Explorer")

                        selected_player = st.selectbox(
                            "Select a player",
                            df["player_name"].tolist(),
                            key="q20_player"
                        )

                        player = df.loc[
                            df["player_name"] == selected_player
                        ].iloc[0]

                        e1, e2, e3, e4 = st.columns(4)

                        with e1:
                            st.metric(
                                "🏏 Test",
                                f"{int(player['test_matches']):,}",
                                f"Avg {player['test_avg']:.2f}"
                                if pd.notna(player["test_avg"])
                                else "Avg N/A"
                            )

                        with e2:
                            st.metric(
                                "🏏 ODI",
                                f"{int(player['odi_matches']):,}",
                                f"Avg {player['odi_avg']:.2f}"
                                if pd.notna(player["odi_avg"])
                                else "Avg N/A"
                            )

                        with e3:
                            st.metric(
                                "⚡ T20I",
                                f"{int(player['t20i_matches']):,}",
                                f"Avg {player['t20i_avg']:.2f}"
                                if pd.notna(player["t20i_avg"])
                                else "Avg N/A"
                            )

                        with e4:
                            st.metric(
                                "🔥 Total",
                                f"{int(player['total_matches']):,}"
                            )

                        explorer = pd.DataFrame({
                            "Format": ["Test", "ODI", "T20I"],
                            "Matches": [
                                player["test_matches"],
                                player["odi_matches"],
                                player["t20i_matches"]
                            ],
                            "Batting Average": [
                                player["test_avg"],
                                player["odi_avg"],
                                player["t20i_avg"]
                            ]
                        })

                        fig = px.bar(
                            explorer,
                            x="Format",
                            y="Matches",
                            text="Matches",
                            title=f"🏏 {selected_player} — Format Profile"
                        )
                        fig.update_traces(texttemplate="%{text:.0f}")
                        fig.update_layout(
                            height=400,
                            yaxis_title="Matches"
                        )
                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                        st.divider()

                        st.markdown("### 🏆 Experience Leaderboard")

                        board = df.copy()
                        board.insert(
                            0,
                            "Rank",
                            range(1, len(board) + 1)
                        )

                        board = board[
                            [
                                "Rank",
                                "player_name",
                                "test_matches",
                                "odi_matches",
                                "t20i_matches",
                                "total_matches",
                                "test_avg",
                                "odi_avg",
                                "t20i_avg"
                            ]
                        ].copy()

                        board.columns = [
                            "Rank",
                            "Player",
                            "Test",
                            "ODI",
                            "T20I",
                            "Total",
                            "Test Avg",
                            "ODI Avg",
                            "T20I Avg"
                        ]

                        st.dataframe(
                            board,
                            use_container_width=True,
                            hide_index=True,
                            height=430
                        )

                        st.success(
                            f"👑 **{experience_leader['player_name']} leads the "
                            f"three-format experience battle with "
                            f"{int(experience_leader['total_matches']):,} total matches.**"
                        )

                        st.download_button(
                            "Download results as CSV",
                            df.to_csv(index=False),
                            file_name="Q20_format_experience.csv",
                            mime="text/csv"
                        )


            elif choice.startswith("Q21:"):

                st.subheader("🏆 Top Performers by Format")
                st.caption(
                    "Weighted performance rankings across Test, ODI and T20I • "
                    "Players with zero or missing scores are excluded."
                )

                df = df.copy()

                if df.empty:

                    st.info(
                        "No qualifying player records were found."
                    )

                else:

                    df["format"] = (
                        df["format"]
                        .replace({"IT20": "T20I"})
                        .astype(str)
                        .str.strip()
                    )

                    df["score"] = pd.to_numeric(
                        df["score"],
                        errors="coerce"
                    )

                    df["rank"] = pd.to_numeric(
                        df["rank"],
                        errors="coerce"
                    )

                    df = (
                        df[df["score"] > 0]
                        .dropna(subset=["rank", "score"])
                        .copy()
                    )

                    if df.empty:

                        st.info(
                            "No players have a positive weighted performance score."
                        )

                    else:

                        df["rank"] = df["rank"].astype(int)

                        formats = [
                            "Test",
                            "ODI",
                            "T20I"
                        ]

                        available_formats = [
                            fmt
                            for fmt in formats
                            if fmt in df["format"].unique()
                        ]

                        leaders = {}

                        for format_name in available_formats:

                            format_df = (
                                df[
                                    df["format"] == format_name
                                ]
                                .sort_values(
                                    ["rank", "score"],
                                    ascending=[True, False]
                                )
                            )

                            if not format_df.empty:
                                leaders[format_name] = format_df.iloc[0]

                        st.html(
                            f"""
                            <div style="
                                padding:30px;
                                border-radius:22px;
                                border:1px solid rgba(255,215,0,0.35);
                                text-align:center;
                                margin:5px 0 22px 0;
                                background:
                                    linear-gradient(
                                        135deg,
                                        rgba(255,215,0,0.16),
                                        rgba(255,255,255,0.035)
                                    );
                                box-shadow:
                                    0 8px 30px rgba(0,0,0,0.16);
                            ">
                                <div style="
                                    font-size:52px;
                                    line-height:1;
                                ">
                                    🏆
                                </div>

                                <div style="
                                    font-size:13px;
                                    letter-spacing:3px;
                                    opacity:0.7;
                                    margin-top:10px;
                                ">
                                    PERFORMANCE CHAMPIONS
                                </div>

                                <div style="
                                    font-size:32px;
                                    font-weight:800;
                                    margin:9px 0;
                                ">
                                    Test • ODI • T20I
                                </div>

                                <div style="
                                    font-size:14px;
                                    opacity:0.72;
                                ">
                                    {len(df):,} meaningful player-format rankings
                                </div>
                            </div>
                            """
                        )

                        card_cols = st.columns(4)

                        card_cols[0].metric(
                            "👥 Ranked Records",
                            f"{len(df):,}"
                        )

                        for index, format_name in enumerate(
                            available_formats[:3],
                            start=1
                        ):

                            leader = leaders.get(format_name)

                            if leader is not None:

                                icon = {
                                    "Test": "🟥",
                                    "ODI": "🟦",
                                    "T20I": "🟩"
                                }.get(
                                    format_name,
                                    "🏏"
                                )

                                card_cols[index].metric(
                                    f"{icon} {format_name} Champion",
                                    str(leader["player_name"]),
                                    f"{float(leader['score']):.2f}"
                                )

                            else:

                                card_cols[index].metric(
                                    f"{format_name} Champion",
                                    "—"
                                )

                        st.divider()

                        st.markdown(
                            "### 🎮 Choose Your Arena"
                        )

                        selected_format = st.radio(
                            "Format",
                            available_formats,
                            horizontal=True,
                            key="q21_format_filter",
                            label_visibility="collapsed"
                        )

                        arena_df = (
                            df[
                                df["format"] == selected_format
                            ]
                            .sort_values(
                                ["rank", "score"],
                                ascending=[True, False]
                            )
                            .reset_index(drop=True)
                        )

                        if not arena_df.empty:

                            champion = arena_df.iloc[0]
                            runner_up = (
                                arena_df.iloc[1]
                                if len(arena_df) > 1
                                else None
                            )
                            third_place = (
                                arena_df.iloc[2]
                                if len(arena_df) > 2
                                else None
                            )

                            st.markdown(
                                f"### 🥇 {selected_format} Podium"
                            )

                            podium = [
                                (
                                    champion,
                                    "🥇",
                                    "CHAMPION"
                                ),
                                (
                                    runner_up,
                                    "🥈",
                                    "RUNNER-UP"
                                ),
                                (
                                    third_place,
                                    "🥉",
                                    "THIRD PLACE"
                                )
                            ]

                            podium_cols = st.columns(3)

                            for col, item in zip(
                                podium_cols,
                                podium
                            ):

                                player, medal, label = item

                                with col:

                                    if player is None:

                                        st.info(
                                            f"{medal} {label}"
                                        )

                                    else:

                                        player_name = html.escape(
                                            str(player["player_name"])
                                        )

                                        score = float(
                                            player["score"]
                                        )

                                        st.html(
                                            f"""
                                            <div style="
                                                padding:22px;
                                                border:1px solid #d9d9d9;
                                                border-radius:18px;
                                                text-align:center;
                                                min-height:190px;
                                                box-sizing:border-box;
                                            ">
                                                <div style="
                                                    font-size:38px;
                                                ">
                                                    {medal}
                                                </div>

                                                <div style="
                                                    font-size:11px;
                                                    letter-spacing:2px;
                                                    opacity:0.65;
                                                    margin-top:4px;
                                                ">
                                                    {label}
                                                </div>

                                                <div style="
                                                    font-size:19px;
                                                    font-weight:700;
                                                    margin:10px 0;
                                                ">
                                                    {player_name}
                                                </div>

                                                <div style="
                                                    font-size:26px;
                                                    font-weight:800;
                                                ">
                                                    {score:.2f}
                                                </div>

                                                <div style="
                                                    font-size:11px;
                                                    opacity:0.65;
                                                ">
                                                    weighted score
                                                </div>
                                            </div>
                                            """
                                        )

                            st.divider()

                            st.markdown(
                                "### 📊 Performance Battle"
                            )

                            chart_mode = st.radio(
                                "Chart view",
                                [
                                    "Full Ranking",
                                    "Top 25",
                                    "Top 10"
                                ],
                                horizontal=True,
                                key="q21_chart_mode"
                            )

                            if chart_mode == "Top 10":

                                chart_df = arena_df.head(10).copy()

                            elif chart_mode == "Top 25":

                                chart_df = arena_df.head(25).copy()

                            else:

                                chart_df = arena_df.copy()

                            chart_df = chart_df.sort_values(
                                "score",
                                ascending=True
                            )

                            chart = px.bar(
                                chart_df,
                                x="score",
                                y="player_name",
                                orientation="h",
                                text="score",
                                hover_data=["rank"],
                                labels={
                                    "score": "Weighted Performance Score",
                                    "player_name": "Player",
                                    "rank": "Rank"
                                }
                            )

                            chart.update_traces(
                                texttemplate="%{text:.2f}",
                                textposition="outside"
                            )

                            chart.update_layout(
                                height=max(
                                    450,
                                    min(950, len(chart_df) * 38)
                                ),
                                margin=dict(
                                    l=20,
                                    r=90,
                                    t=20,
                                    b=20
                                ),
                                yaxis={
                                    "categoryorder": "array",
                                    "categoryarray": chart_df[
                                        "player_name"
                                    ].tolist()
                                }
                            )

                            st.plotly_chart(
                                chart,
                                use_container_width=True,
                                key="q21_performance_chart"
                            )

                            st.divider()

                            st.markdown(
                                "### 🔎 Player Explorer"
                            )

                            player_options = (
                                arena_df[
                                    "player_name"
                                ]
                                .drop_duplicates()
                                .tolist()
                            )

                            selected_player = st.selectbox(
                                "Select a player",
                                player_options,
                                key="q21_player_explorer"
                            )

                            player_row = arena_df[
                                arena_df["player_name"] == selected_player
                            ].iloc[0]

                            explorer_cols = st.columns(4)

                            explorer_cols[0].metric(
                                "🏅 Rank",
                                f"#{int(player_row['rank'])}"
                            )

                            explorer_cols[1].metric(
                                "⚡ Score",
                                f"{float(player_row['score']):.2f}"
                            )

                            explorer_cols[2].metric(
                                "🏏 Format",
                                selected_format
                            )

                            explorer_cols[3].metric(
                                "👥 Players Ranked",
                                f"{len(arena_df):,}"
                            )

                            max_score = max(
                                float(arena_df["score"].max()),
                                1.0
                            )

                            relative_power = (
                                float(player_row["score"])
                                / max_score
                            )

                            st.progress(
                                min(
                                    max(
                                        relative_power,
                                        0
                                    ),
                                    1
                                )
                            )

                            st.caption(
                                f"⚡ Relative performance power: "
                                f"{relative_power * 100:.1f}% of the "
                                f"{selected_format} leader"
                            )

                            st.divider()

                            st.markdown(
                                f"### 🏅 {selected_format} Leaderboard"
                            )

                            leaderboard_df = arena_df[
                                [
                                    "rank",
                                    "player_name",
                                    "format",
                                    "score"
                                ]
                            ].copy()

                            leaderboard_df.columns = [
                                "Rank",
                                "Player",
                                "Format",
                                "Performance Score"
                            ]

                            st.dataframe(
                                leaderboard_df,
                                use_container_width=True,
                                hide_index=True,
                                height=550,
                                column_config={
                                    "Rank":
                                        st.column_config.NumberColumn(
                                            "Rank",
                                            format="%d"
                                        ),
                                    "Performance Score":
                                        st.column_config.NumberColumn(
                                            "Performance Score",
                                            format="%.2f"
                                        )
                                }
                            )

                            st.divider()

                            st.markdown(
                                "### ⚔️ Three-Format Comparison"
                            )

                            st.caption(
                                "Players are shown only where the database "
                                "contains a positive weighted score."
                            )

                            comparison = (
                                df.pivot_table(
                                    index="player_name",
                                    columns="format",
                                    values="score",
                                    aggfunc="max"
                                )
                                .reindex(columns=formats)
                            )

                            comparison["Formats Ranked"] = (
                                comparison[
                                    formats
                                ]
                                .notna()
                                .sum(axis=1)
                            )

                            comparison["Best Score"] = (
                                comparison[
                                    formats
                                ]
                                .max(axis=1)
                            )

                            comparison = comparison.sort_values(
                                "Best Score",
                                ascending=False
                            )

                            comparison_view = comparison.reset_index()
                            comparison_view.columns.name = None
                            comparison_view = comparison_view.rename(
                                columns={
                                    "player_name": "Player"
                                }
                            )

                            st.dataframe(
                                comparison_view,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Test":
                                        st.column_config.NumberColumn(
                                            "Test",
                                            format="%.2f"
                                        ),
                                    "ODI":
                                        st.column_config.NumberColumn(
                                            "ODI",
                                            format="%.2f"
                                        ),
                                    "T20I":
                                        st.column_config.NumberColumn(
                                            "T20I",
                                            format="%.2f"
                                        ),
                                    "Best Score":
                                        st.column_config.NumberColumn(
                                            "Best Score",
                                            format="%.2f"
                                        )
                                }
                            )

                            st.download_button(
                                "⬇️ Download Q21 Rankings",
                                df.to_csv(index=False),
                                file_name="Q21_top_performers_by_format.csv",
                                mime="text/csv"
                            )

            elif choice.startswith("Q22:"):

                st.subheader("⚔️ H2H Battle Arena")
                st.caption(
                    "Last 3 years • minimum 5 meetings • historical head-to-head analysis"
                )

                summary_df = df.copy()
                venue_df = st.session_state.get(
                    "q22_venue_result",
                    pd.DataFrame()
                )

                if venue_df is None:
                    venue_df = pd.DataFrame()

                if summary_df.empty:
                    st.info("No qualifying head-to-head matchups were found.")
                else:
                    # Clean numeric columns used by the interactive experience.
                    numeric_summary_columns = [
                        "total_matches",
                        "team_a_wins",
                        "team_b_wins",
                        "team_a_win_percentage",
                        "team_b_win_percentage",
                        "team_a_avg_victory_margin",
                        "team_b_avg_victory_margin"
                    ]

                    for column in numeric_summary_columns:
                        if column in summary_df.columns:
                            summary_df[column] = pd.to_numeric(
                                summary_df[column],
                                errors="coerce"
                            )

                    # Quick matchup buttons.
                    st.markdown("### 🎮 Quick Matchups")
                    st.caption(
                        "Click a matchup to open its head-to-head battle card."
                    )

                    quick_df = (
                        summary_df
                        .sort_values(
                            ["total_matches", "team_a_win_percentage"],
                            ascending=[False, False]
                        )
                        .head(12)
                        .reset_index(drop=True)
                    )

                    if "q22_selected_pair" not in st.session_state:
                        st.session_state["q22_selected_pair"] = (
                            str(quick_df.iloc[0]["team_a"]),
                            str(quick_df.iloc[0]["team_b"])
                        )

                    for row_start in range(0, len(quick_df), 4):
                        button_cols = st.columns(4)

                        for button_col, (_, row) in zip(
                            button_cols,
                            quick_df.iloc[row_start:row_start + 4].iterrows()
                        ):
                            team_a = str(row["team_a"])
                            team_b = str(row["team_b"])
                            pair_key = (team_a, team_b)

                            with button_col:
                                if st.button(
                                    f"🏏 {team_a} vs {team_b}",
                                    key=f"q22_pair_{row_start}_{team_a}_{team_b}",
                                    use_container_width=True
                                ):
                                    selected_button_label = f"{team_a} vs {team_b}"
                                    st.session_state["q22_selected_pair"] = pair_key
                                    st.session_state["q22_matchup_selector"] = selected_button_label
                                    st.rerun()

                    st.divider()

                    # All qualifying matchups selector.
                    pair_labels = [
                        f"{row['team_a']} vs {row['team_b']}"
                        for _, row in summary_df.iterrows()
                    ]

                    selected_pair = st.session_state["q22_selected_pair"]
                    selected_label = (
                        f"{selected_pair[0]} vs {selected_pair[1]}"
                    )

                    if selected_label not in pair_labels:
                        selected_label = pair_labels[0]
                        selected_row = summary_df.iloc[0]
                        st.session_state["q22_selected_pair"] = (
                            str(selected_row["team_a"]),
                            str(selected_row["team_b"])
                        )

                    selected_label = st.selectbox(
                        "🔎 Choose any qualifying matchup",
                        pair_labels,
                        index=pair_labels.index(selected_label),
                        key="q22_matchup_selector"
                    )

                    selected_team_a, selected_team_b = selected_label.split(
                        " vs ",
                        1
                    )

                    st.session_state["q22_selected_pair"] = (
                        selected_team_a,
                        selected_team_b
                    )

                    selected_row = summary_df[
                        (summary_df["team_a"].astype(str) == selected_team_a)
                        & (summary_df["team_b"].astype(str) == selected_team_b)
                    ].iloc[0]

                    team_a_wins = int(selected_row["team_a_wins"])
                    team_b_wins = int(selected_row["team_b_wins"])
                    total_matches = int(selected_row["total_matches"])
                    team_a_pct = float(selected_row["team_a_win_percentage"])
                    team_b_pct = float(selected_row["team_b_win_percentage"])

                    team_a_margin = selected_row["team_a_avg_victory_margin"]
                    team_b_margin = selected_row["team_b_avg_victory_margin"]

                    # Historical prediction card.
                    if team_a_pct > team_b_pct:
                        predicted_team = selected_team_a
                        prediction_pct = team_a_pct
                    elif team_b_pct > team_a_pct:
                        predicted_team = selected_team_b
                        prediction_pct = team_b_pct
                    else:
                        predicted_team = "Too close to call"
                        prediction_pct = 50.0

                    st.html(
                        f"""
                        <div style="
                            padding:28px;
                            border-radius:20px;
                            border:1px solid #d9d9d9;
                            text-align:center;
                            margin:8px 0 20px 0;
                            background:linear-gradient(
                                135deg,
                                rgba(255,153,51,0.16),
                                rgba(60,120,255,0.10)
                            );
                        ">
                            <div style="
                                font-size:13px;
                                letter-spacing:2px;
                                opacity:0.7;
                            ">
                                🧠 HISTORICAL MATCH PREDICTION
                            </div>

                            <div style="
                                font-size:34px;
                                font-weight:800;
                                margin:10px 0;
                            ">
                                {predicted_team}
                            </div>

                            <div style="
                                font-size:16px;
                                opacity:0.78;
                            ">
                                Historical H2H edge: {prediction_pct:.1f}%
                            </div>

                            <div style="
                                font-size:12px;
                                opacity:0.62;
                                margin-top:8px;
                            ">
                                Based on the last 3 years of qualifying H2H results —
                                not a live prediction model.
                            </div>
                        </div>
                        """
                    )

                    # Core battle metrics.
                    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

                    with metric_1:
                        st.metric(
                            "🏟️ Meetings",
                            total_matches
                        )

                    with metric_2:
                        st.metric(
                            f"🏆 {selected_team_a} Wins",
                            team_a_wins,
                            f"{team_a_pct:.1f}%"
                        )

                    with metric_3:
                        st.metric(
                            f"🏆 {selected_team_b} Wins",
                            team_b_wins,
                            f"{team_b_pct:.1f}%"
                        )

                    with metric_4:
                        margin_text = (
                            f"{team_a_margin:.1f} / {team_b_margin:.1f}"
                            if pd.notna(team_a_margin)
                            and pd.notna(team_b_margin)
                            else "N/A"
                        )
                        st.metric(
                            "📏 Avg Victory Margin",
                            margin_text,
                            f"{selected_team_a} / {selected_team_b}"
                        )

                    st.divider()

                    # H2H win chart.
                    st.markdown("### 🥊 Head-to-Head Win Battle")

                    win_chart_df = pd.DataFrame({
                        "Team": [selected_team_a, selected_team_b],
                        "Wins": [team_a_wins, team_b_wins]
                    })

                    win_chart = px.bar(
                        win_chart_df,
                        x="Team",
                        y="Wins",
                        text="Wins",
                        title="Historical Wins",
                        template="plotly_white"
                    )

                    win_chart.update_traces(
                        hovertemplate="<b>%{x}</b><br>Wins: %{y}<extra></extra>"
                    )
                    win_chart.update_layout(
                        height=380,
                        showlegend=False,
                        margin=dict(l=20, r=20, t=60, b=20)
                    )

                    st.plotly_chart(
                        win_chart,
                        use_container_width=True
                    )

                    # Venue performance for selected pair only.
                    if not venue_df.empty:
                        pair_venue_df = venue_df[
                            (venue_df["team_a"].astype(str) == selected_team_a)
                            & (venue_df["team_b"].astype(str) == selected_team_b)
                        ].copy()

                        if not pair_venue_df.empty:
                            st.divider()
                            st.markdown("### 🏟️ Venue Battle")

                            venue_options = (
                                pair_venue_df["venue_name"]
                                .fillna("Unknown venue")
                                .astype(str)
                                .drop_duplicates()
                                .tolist()
                            )

                            selected_venue = st.selectbox(
                                "📍 Select a venue",
                                ["All venues"] + venue_options,
                                key="q22_venue_selector"
                            )

                            if selected_venue != "All venues":
                                selected_venue_df = pair_venue_df[
                                    pair_venue_df["venue_name"].astype(str)
                                    == selected_venue
                                ].copy()
                            else:
                                selected_venue_df = pair_venue_df.copy()

                            # Batting-first comparison.
                            bat_chart_df = pd.DataFrame({
                                "Team": [
                                    selected_team_a,
                                    selected_team_b
                                ],
                                "Win %": [
                                    selected_venue_df["team_a_batting_first_win_pct"].iloc[0]
                                    if pd.notna(
                                        selected_venue_df["team_a_batting_first_win_pct"].iloc[0]
                                    )
                                    else 0,
                                    selected_venue_df["team_b_batting_first_win_pct"].iloc[0]
                                    if pd.notna(
                                        selected_venue_df["team_b_batting_first_win_pct"].iloc[0]
                                    )
                                    else 0
                                ]
                            })

                            # Bowling-first comparison.
                            bowl_chart_df = pd.DataFrame({
                                "Team": [
                                    selected_team_a,
                                    selected_team_b
                                ],
                                "Win %": [
                                    selected_venue_df["team_a_bowling_first_win_pct"].iloc[0]
                                    if pd.notna(
                                        selected_venue_df["team_a_bowling_first_win_pct"].iloc[0]
                                    )
                                    else 0,
                                    selected_venue_df["team_b_bowling_first_win_pct"].iloc[0]
                                    if pd.notna(
                                        selected_venue_df["team_b_bowling_first_win_pct"].iloc[0]
                                    )
                                    else 0
                                ]
                            })

                            bat_col, bowl_col = st.columns(2)

                            with bat_col:
                                st.markdown("#### 🏏 Batting First")
                                bat_chart = px.bar(
                                    bat_chart_df,
                                    x="Team",
                                    y="Win %",
                                    text="Win %",
                                    range_y=[0, 100],
                                    title="Win % When Batting First",
                                    template="plotly_white"
                                )
                                bat_chart.update_traces(
                                    texttemplate="%{text:.1f}%",
                                    hovertemplate="<b>%{x}</b><br>Win %: %{y:.1f}%<extra></extra>"
                                )
                                bat_chart.update_layout(
                                    height=360,
                                    showlegend=False,
                                    margin=dict(l=10, r=10, t=60, b=20)
                                )
                                st.plotly_chart(
                                    bat_chart,
                                    use_container_width=True
                                )

                            with bowl_col:
                                st.markdown("#### 🎯 Bowling First")
                                bowl_chart = px.bar(
                                    bowl_chart_df,
                                    x="Team",
                                    y="Win %",
                                    text="Win %",
                                    range_y=[0, 100],
                                    title="Win % When Bowling First",
                                    template="plotly_white"
                                )
                                bowl_chart.update_traces(
                                    texttemplate="%{text:.1f}%",
                                    hovertemplate="<b>%{x}</b><br>Win %: %{y:.1f}%<extra></extra>"
                                )
                                bowl_chart.update_layout(
                                    height=360,
                                    showlegend=False,
                                    margin=dict(l=10, r=10, t=60, b=20)
                                )
                                st.plotly_chart(
                                    bowl_chart,
                                    use_container_width=True
                                )

                            # Venue map uses country-level coordinates supplied by Plotly.
                            # The database has venue country but not latitude/longitude,
                            # so this avoids inventing venue coordinates.
                            if "country" in selected_venue_df.columns:
                                map_df = (
                                    selected_venue_df
                                    .dropna(subset=["country"])
                                    .groupby("country", as_index=False)
                                    .agg(
                                        venue_matches=("matches_at_venue", "sum")
                                    )
                                )

                                if not map_df.empty:
                                    st.markdown("### 🌍 Venue Battle Map")
                                    st.caption(
                                        "Interactive map at country level because the "
                                        "database does not store venue latitude/longitude."
                                    )

                                    map_chart = px.scatter_geo(
                                        map_df,
                                        locations="country",
                                        locationmode="country names",
                                        size="venue_matches",
                                        hover_name="country",
                                        hover_data={
                                            "venue_matches": True
                                        },
                                        projection="natural earth",
                                        title=(
                                            f"{selected_team_a} vs "
                                            f"{selected_team_b} — H2H Venues"
                                        ),
                                        template="plotly_white"
                                    )

                                    map_chart.update_layout(
                                        height=520,
                                        margin=dict(l=0, r=0, t=60, b=0)
                                    )

                                    st.plotly_chart(
                                        map_chart,
                                        use_container_width=True
                                    )

                            # Venue detail table.
                            st.markdown("### 📋 Venue Performance Details")

                            venue_display = selected_venue_df[[
                                "venue_name",
                                "matches_at_venue",
                                "team_a_batting_first_matches",
                                "team_a_batting_first_wins",
                                "team_a_batting_first_win_pct",
                                "team_a_bowling_first_matches",
                                "team_a_bowling_first_wins",
                                "team_a_bowling_first_win_pct",
                                "team_b_batting_first_matches",
                                "team_b_batting_first_wins",
                                "team_b_batting_first_win_pct",
                                "team_b_bowling_first_matches",
                                "team_b_bowling_first_wins",
                                "team_b_bowling_first_win_pct"
                            ]].copy()

                            venue_display = venue_display.rename(
                                columns={
                                    "venue_name": "Venue",
                                    "matches_at_venue": "Matches",
                                    "team_a_batting_first_matches": f"{selected_team_a} Bat First Matches",
                                    "team_a_batting_first_wins": f"{selected_team_a} Bat First Wins",
                                    "team_a_batting_first_win_pct": f"{selected_team_a} Bat First Win %",
                                    "team_a_bowling_first_matches": f"{selected_team_a} Bowl First Matches",
                                    "team_a_bowling_first_wins": f"{selected_team_a} Bowl First Wins",
                                    "team_a_bowling_first_win_pct": f"{selected_team_a} Bowl First Win %",
                                    "team_b_batting_first_matches": f"{selected_team_b} Bat First Matches",
                                    "team_b_batting_first_wins": f"{selected_team_b} Bat First Wins",
                                    "team_b_batting_first_win_pct": f"{selected_team_b} Bat First Win %",
                                    "team_b_bowling_first_matches": f"{selected_team_b} Bowl First Matches",
                                    "team_b_bowling_first_wins": f"{selected_team_b} Bowl First Wins",
                                    "team_b_bowling_first_win_pct": f"{selected_team_b} Bowl First Win %"
                                }
                            )

                            st.dataframe(
                                venue_display,
                                use_container_width=True,
                                hide_index=True,
                                height=420
                            )

                        else:
                            st.info(
                                "No mapped venue performance is available for this matchup."
                            )
                    else:
                        st.info(
                            "Venue performance data was not returned. "
                            "Run Q22 again to refresh it."
                        )

                    st.divider()

                    # Full qualifying matchup leaderboard.
                    st.markdown("### 🏆 H2H Leaderboard")

                    leaderboard_df = summary_df.copy()

                    leaderboard_df["H2H Edge"] = leaderboard_df.apply(
                        lambda row: (
                            row["team_a"]
                            if row["team_a_win_percentage"]
                            > row["team_b_win_percentage"]
                            else row["team_b"]
                            if row["team_b_win_percentage"]
                            > row["team_a_win_percentage"]
                            else "Even"
                        ),
                        axis=1
                    )

                    leaderboard_df = leaderboard_df.rename(
                        columns={
                            "team_a": "Team A",
                            "team_b": "Team B",
                            "total_matches": "Matches",
                            "team_a_wins": "A Wins",
                            "team_b_wins": "B Wins",
                            "team_a_win_percentage": "A Win %",
                            "team_b_win_percentage": "B Win %",
                            "team_a_avg_victory_margin": "A Avg Margin",
                            "team_b_avg_victory_margin": "B Avg Margin"
                        }
                    )

                    leaderboard_df = leaderboard_df[[
                        "Team A",
                        "Team B",
                        "Matches",
                        "A Wins",
                        "B Wins",
                        "A Win %",
                        "B Win %",
                        "A Avg Margin",
                        "B Avg Margin",
                        "H2H Edge"
                    ]]

                    st.dataframe(
                        leaderboard_df,
                        use_container_width=True,
                        hide_index=True,
                        height=520
                    )

                    st.download_button(
                        "⬇️ Download Q22 H2H Summary",
                        summary_df.to_csv(index=False),
                        file_name="Q22_h2h_summary.csv",
                        mime="text/csv"
                    )

                    if not venue_df.empty:
                        st.download_button(
                            "⬇️ Download Q22 Venue Performance",
                            venue_df.to_csv(index=False),
                            file_name="Q22_venue_performance.csv",
                            mime="text/csv"
                        )

            elif choice.startswith("Q23:"):

                st.subheader("🔥 Form & Momentum Arena")
                st.caption(
                    "Last 10 batting innings • active players • "
                    "metrics-driven form classification"
                )

                q23 = df.copy()

                if q23.empty:
                    st.info("No qualifying player form data was found.")
                else:
                    numeric_cols = [
                        "avg_last_5", "avg_last_10",
                        "strike_rate_last_5", "strike_rate_last_10",
                        "strike_rate_trend", "scores_50_plus",
                        "stddev_runs", "consistency_score"
                    ]

                    for col in numeric_cols:
                        if col in q23.columns:
                            q23[col] = pd.to_numeric(
                                q23[col], errors="coerce"
                            ).fillna(0)

                    q23["form_category"] = (
                        q23["form_category"]
                        .fillna("Poor Form")
                        .astype(str)
                    )

                    categories = [
                        "All",
                        "Excellent Form",
                        "Good Form",
                        "Average Form",
                        "Poor Form"
                    ]

                    if "q23_form_filter" not in st.session_state:
                        st.session_state["q23_form_filter"] = "All"

                    st.markdown("### 🎮 Choose Your Form Tier")

                    button_cols = st.columns(5)

                    for col, category in zip(button_cols, categories):
                        with col:
                            if st.button(
                                category,
                                key=f"q23_filter_{category}",
                                use_container_width=True,
                                type=(
                                    "primary"
                                    if st.session_state["q23_form_filter"] == category
                                    else "secondary"
                                )
                            ):
                                st.session_state["q23_form_filter"] = category

                    selected_category = st.session_state["q23_form_filter"]

                    display_df = (
                        q23
                        if selected_category == "All"
                        else q23[
                            q23["form_category"] == selected_category
                        ]
                    ).copy()

                    category_counts = (
                        q23["form_category"]
                        .value_counts()
                        .reindex(categories[1:], fill_value=0)
                    )

                    excellent_count = int(
                        category_counts.get("Excellent Form", 0)
                    )
                    good_count = int(
                        category_counts.get("Good Form", 0)
                    )
                    average_count = int(
                        category_counts.get("Average Form", 0)
                    )
                    poor_count = int(
                        category_counts.get("Poor Form", 0)
                    )

                    st.divider()

                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.metric("🔥 Excellent", excellent_count)

                    with col2:
                        st.metric("⚡ Good", good_count)

                    with col3:
                        st.metric("📈 Average", average_count)

                    with col4:
                        st.metric("📉 Poor", poor_count)

                    with col5:
                        st.metric("🏏 Players", len(q23))

                    st.divider()

                    st.markdown(
                        f"### 🏆 {selected_category} Leaderboard"
                    )

                    if display_df.empty:
                        st.info(
                            f"No players are currently in {selected_category}."
                        )
                    else:
                        display_df = display_df.sort_values(
                            ["avg_last_5", "consistency_score"],
                            ascending=False
                        ).reset_index(drop=True)

                        top_cols = st.columns(
                            min(3, len(display_df))
                        )

                        for col, (_, player) in zip(
                            top_cols,
                            display_df.head(3).iterrows()
                        ):
                            with col:
                                st.html(
                                    f"""
                                    <div style="
                                        padding:20px;
                                        border:1px solid #d9d9d9;
                                        border-radius:16px;
                                        text-align:center;
                                        min-height:170px;
                                    ">
                                        <div style="font-size:30px;">
                                            🏏
                                        </div>
                                        <div style="
                                            font-size:18px;
                                            font-weight:700;
                                            margin:7px 0;
                                        ">
                                            {html.escape(str(player["player_name"]))}
                                        </div>
                                        <div style="
                                            font-size:13px;
                                            opacity:.7;
                                        ">
                                            {html.escape(str(player["form_category"]))}
                                        </div>
                                        <div style="
                                            font-size:25px;
                                            font-weight:700;
                                            margin-top:10px;
                                        ">
                                            {player["avg_last_5"]:.1f}
                                        </div>
                                        <div style="
                                            font-size:12px;
                                            opacity:.7;
                                        ">
                                            Avg Runs • Last 5
                                        </div>
                                    </div>
                                    """
                                )

                    st.divider()

                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        category_chart_df = (
                            category_counts
                            .rename_axis("Form")
                            .reset_index(name="Players")
                        )

                        fig = px.bar(
                            category_chart_df,
                            x="Form",
                            y="Players",
                            text="Players",
                            title="🏅 Form Tier Distribution",
                            template="plotly_dark"
                        )

                        fig.update_traces(
                            hovertemplate=(
                                "<b>%{x}</b><br>"
                                "Players: %{y}<extra></extra>"
                            )
                        )

                        fig.update_layout(
                            height=380,
                            margin=dict(l=20, r=20, t=60, b=20)
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    with chart_col2:
                        top10 = q23.nlargest(
                            10,
                            "avg_last_5"
                        ).sort_values("avg_last_5")

                        fig = px.bar(
                            top10,
                            x="avg_last_5",
                            y="player_name",
                            orientation="h",
                            text="avg_last_5",
                            title="🔥 Top 10 Recent Run Form",
                            template="plotly_dark"
                        )

                        fig.update_traces(
                            hovertemplate=(
                                "<b>%{y}</b><br>"
                                "Last 5 Avg: %{x:.2f}<extra></extra>"
                            )
                        )

                        fig.update_layout(
                            height=380,
                            margin=dict(l=20, r=20, t=60, b=20)
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

                    st.divider()

                    st.markdown("### 🎯 Consistency vs Recent Form")

                    scatter = px.scatter(
                        q23,
                        x="avg_last_5",
                        y="consistency_score",
                        color="form_category",
                        hover_name="player_name",
                        hover_data={
                            "avg_last_10": ":.2f",
                            "strike_rate_trend": ":.2f",
                            "scores_50_plus": True,
                            "stddev_runs": ":.2f"
                        },
                        title="Form Map",
                        template="plotly_dark"
                    )

                    scatter.update_layout(
                        height=480,
                        margin=dict(l=20, r=20, t=60, b=20),
                        xaxis_title="Average Runs — Last 5",
                        yaxis_title="Consistency Score"
                    )

                    st.plotly_chart(
                        scatter,
                        use_container_width=True
                    )

                    st.divider()

                    st.markdown("### 🔎 Player Spotlight")

                    player_options = display_df["player_name"].tolist()

                    if player_options:
                        selected_player = st.selectbox(
                            "Select a player",
                            player_options,
                            key="q23_player_spotlight"
                        )

                        player_row = display_df[
                            display_df["player_name"] == selected_player
                        ].iloc[0]

                        m1, m2, m3, m4 = st.columns(4)

                        with m1:
                            st.metric(
                                "🔥 Form",
                                player_row["form_category"]
                            )

                        with m2:
                            st.metric(
                                "🏏 Last 5 Avg",
                                f'{player_row["avg_last_5"]:.2f}'
                            )

                        with m3:
                            st.metric(
                                "⚡ SR Trend",
                                f'{player_row["strike_rate_trend"]:+.2f}'
                            )

                        with m4:
                            st.metric(
                                "🎯 Consistency",
                                f'{player_row["consistency_score"]:.1f}'
                            )

                        spotlight_df = pd.DataFrame({
                            "Metric": [
                                "Avg Runs — Last 5",
                                "Avg Runs — Last 10",
                                "SR — Last 5",
                                "SR — Last 10",
                                "50+ Scores",
                                "Consistency"
                            ],
                            "Value": [
                                player_row["avg_last_5"],
                                player_row["avg_last_10"],
                                player_row["strike_rate_last_5"],
                                player_row["strike_rate_last_10"],
                                player_row["scores_50_plus"],
                                player_row["consistency_score"]
                            ]
                        })

                        spotlight_fig = px.bar(
                            spotlight_df,
                            x="Metric",
                            y="Value",
                            text="Value",
                            title=f"📊 {selected_player} — Performance Profile",
                            template="plotly_dark"
                        )

                        spotlight_fig.update_layout(
                            height=400,
                            margin=dict(l=20, r=20, t=60, b=20)
                        )

                        st.plotly_chart(
                            spotlight_fig,
                            use_container_width=True
                        )

                    st.divider()

                    st.markdown("### 📋 Full Form Rankings")

                    table_df = display_df[[
                        "player_name",
                        "avg_last_5",
                        "avg_last_10",
                        "strike_rate_last_5",
                        "strike_rate_last_10",
                        "strike_rate_trend",
                        "scores_50_plus",
                        "stddev_runs",
                        "consistency_score",
                        "form_category"
                    ]].copy()

                    table_df.columns = [
                        "Player",
                        "Last 5 Avg",
                        "Last 10 Avg",
                        "SR — Last 5",
                        "SR — Last 10",
                        "SR Trend",
                        "50+ Scores",
                        "Run Std Dev",
                        "Consistency",
                        "Form"
                    ]

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=520
                    )

                    st.download_button(
                        "⬇️ Download Q23 Form Rankings",
                        table_df.to_csv(index=False),
                        file_name="Q23_recent_form_momentum.csv",
                        mime="text/csv"
                    )

            elif choice.startswith("Q24:"):

                st.subheader("🤝 Batting Partnership Arena")
                st.caption(
                    "Best batting combinations • 5+ partnerships • ranked by partnership performance"
                )

                q24 = df.copy()
                required = [
                    "batter_1", "batter_2", "partnerships_played",
                    "avg_partnership_runs", "partnerships_over_50",
                    "highest_partnership", "success_rate_pct"
                ]
                missing = [c for c in required if c not in q24.columns]

                if missing:
                    st.error("Q24 result is missing required columns: " + ", ".join(missing))
                elif q24.empty:
                    st.info("No qualifying batting partnerships were found.")
                else:
                    for col in required[2:]:
                        q24[col] = pd.to_numeric(q24[col], errors="coerce")
                    q24 = q24.dropna(subset=["batter_1", "batter_2"]).copy()
                    q24["partnership"] = (
                        q24["batter_1"].astype(str) + " & " + q24["batter_2"].astype(str)
                    )

                    modes = [
                        "🏏 Average Runs", "🔥 50+ Partnerships",
                        "💥 Highest Partnership", "🎯 Success Rate"
                    ]
                    if "q24_mode" not in st.session_state:
                        st.session_state["q24_mode"] = modes[0]

                    st.markdown("### 🎮 Choose Your Arena")
                    button_cols = st.columns(4)
                    for col, mode_name in zip(button_cols, modes):
                        with col:
                            if st.button(
                                mode_name,
                                key=f"q24_mode_{mode_name}",
                                use_container_width=True,
                                type=("primary" if st.session_state["q24_mode"] == mode_name else "secondary")
                            ):
                                st.session_state["q24_mode"] = mode_name
                                st.rerun()

                    mode = st.session_state["q24_mode"]
                    sort_col = {
                        modes[0]: "avg_partnership_runs",
                        modes[1]: "partnerships_over_50",
                        modes[2]: "highest_partnership",
                        modes[3]: "success_rate_pct"
                    }[mode]
                    q24 = q24.sort_values(
                        [sort_col, "partnerships_played"], ascending=[False, False]
                    ).reset_index(drop=True)

                    crown = q24.iloc[0]
                    crown_title = {
                        modes[0]: "PARTNERSHIP RUN KING",
                        modes[1]: "50+ PARTNERSHIP KING",
                        modes[2]: "HIGHEST PARTNERSHIP KING",
                        modes[3]: "PARTNERSHIP SUCCESS KING"
                    }[mode]
                    crown_value = {
                        modes[0]: f"{crown['avg_partnership_runs']:.2f} AVG RUNS",
                        modes[1]: f"{int(crown['partnerships_over_50']):,} 50+ PARTNERSHIPS",
                        modes[2]: f"{int(crown['highest_partnership']):,} RUNS",
                        modes[3]: f"{crown['success_rate_pct']:.2f}% SUCCESS RATE"
                    }[mode]

                    st.html(
                        f"""
                        <div style="padding:28px;border-radius:20px;border:1px solid rgba(255,215,0,.35);text-align:center;margin:8px 0 20px 0;background:linear-gradient(135deg,rgba(255,215,0,.16),rgba(255,255,255,.035));box-shadow:0 8px 30px rgba(0,0,0,.16);">
                            <div style="font-size:46px;">👑</div>
                            <div style="font-size:12px;letter-spacing:3px;opacity:.7;">{crown_title}</div>
                            <div style="font-size:29px;font-weight:800;margin:8px 0;">{html.escape(str(crown['partnership']))}</div>
                            <div style="font-size:22px;font-weight:700;">{crown_value}</div>
                            <div style="font-size:13px;opacity:.7;margin-top:6px;">{int(crown['partnerships_played']):,} partnerships played</div>
                        </div>
                        """
                    )

                    leaders = {
                        "avg": q24.loc[q24["avg_partnership_runs"].idxmax()],
                        "50": q24.loc[q24["partnerships_over_50"].idxmax()],
                        "high": q24.loc[q24["highest_partnership"].idxmax()],
                        "success": q24.loc[q24["success_rate_pct"].idxmax()]
                    }
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🏏 Best Avg Runs", f"{leaders['avg']['avg_partnership_runs']:.2f}")
                    c2.metric("🔥 Most 50+", f"{int(leaders['50']['partnerships_over_50']):,}")
                    c3.metric("💥 Highest Stand", f"{int(leaders['high']['highest_partnership']):,}")
                    c4.metric("🎯 Best Success", f"{leaders['success']['success_rate_pct']:.2f}%")

                    st.divider()
                    st.markdown("### 📊 Partnership Performance Battle")
                    chart_df = q24.head(15).sort_values(sort_col)
                    chart = px.bar(
                        chart_df, x=sort_col, y="partnership", orientation="h", text=sort_col,
                        hover_data={
                            "partnerships_played": True,
                            "avg_partnership_runs": ":.2f",
                            "partnerships_over_50": True,
                            "highest_partnership": True,
                            "success_rate_pct": ":.2f"
                        },
                        labels={sort_col: mode.split(" ", 1)[1], "partnership": "Partnership"},
                        title=f"{mode} — Top 15"
                    )
                    chart.update_traces(
                        texttemplate=("%{text:.2f}" if sort_col in ["avg_partnership_runs", "success_rate_pct"] else "%{text:.0f}"),
                        textposition="outside"
                    )
                    chart.update_layout(
                        height=max(450, min(800, len(chart_df) * 38)),
                        margin=dict(l=20, r=80, t=60, b=20), showlegend=False
                    )
                    st.plotly_chart(chart, use_container_width=True, key="q24_performance_chart")

                    st.divider()
                    st.markdown("### 🥇 Partnership Podium")
                    podium = q24.head(3)
                    cols = st.columns(len(podium))
                    for col, (_, row), medal in zip(cols, podium.iterrows(), ["🥇", "🥈", "🥉"]):
                        with col:
                            value = row[sort_col]
                            value_text = f"{value:.2f}" if sort_col in ["avg_partnership_runs", "success_rate_pct"] else f"{int(value):,}"
                            st.html(
                                f"""
                                <div style="padding:18px;border:1px solid #d9d9d9;border-radius:16px;text-align:center;min-height:185px;">
                                    <div style="font-size:32px;">{medal}</div>
                                    <div style="font-size:17px;font-weight:700;margin:7px 0;">{html.escape(str(row['partnership']))}</div>
                                    <div style="font-size:25px;font-weight:800;">{value_text}</div>
                                    <div style="font-size:11px;opacity:.7;">{mode.split(' ', 1)[1]}</div>
                                </div>
                                """
                            )

                    st.divider()
                    st.markdown("### 🔎 Partnership Explorer")
                    selected = st.selectbox(
                        "Select a batting partnership", q24["partnership"].tolist(), key="q24_partnership_explorer"
                    )
                    pair = q24[q24["partnership"] == selected].iloc[0]
                    e1, e2, e3, e4 = st.columns(4)
                    e1.metric("🤝 Partnerships", f"{int(pair['partnerships_played']):,}")
                    e2.metric("🏏 Avg Runs", f"{pair['avg_partnership_runs']:.2f}")
                    e3.metric("🔥 50+ Stands", f"{int(pair['partnerships_over_50']):,}")
                    e4.metric("💥 Highest", f"{int(pair['highest_partnership']):,}")

                    profile = pd.DataFrame({
                        "Metric": ["Average Runs", "50+ Partnerships", "Highest Partnership", "Success Rate"],
                        "Value": [pair["avg_partnership_runs"], pair["partnerships_over_50"], pair["highest_partnership"], pair["success_rate_pct"]]
                    })
                    profile_chart = px.bar(
                        profile, x="Metric", y="Value", text="Value",
                        title=f"📊 {selected} — Partnership Profile"
                    )
                    profile_chart.update_layout(height=400, margin=dict(l=20, r=20, t=60, b=20))
                    st.plotly_chart(profile_chart, use_container_width=True, key="q24_profile_chart")

                    st.divider()
                    st.markdown("### 🏆 Full Partnership Rankings")
                    table_df = q24[[
                        "partnership", "partnerships_played", "avg_partnership_runs",
                        "partnerships_over_50", "highest_partnership", "success_rate_pct"
                    ]].copy()
                    table_df.insert(0, "Rank", range(1, len(table_df) + 1))
                    table_df.columns = [
                        "Rank", "Batting Partnership", "Partnerships Played",
                        "Average Partnership Runs", "50+ Partnerships",
                        "Highest Partnership", "Success Rate (%)"
                    ]
                    st.dataframe(
                        table_df, use_container_width=True, hide_index=True, height=520,
                        column_config={
                            "Rank": st.column_config.NumberColumn("Rank", format="%d"),
                            "Average Partnership Runs": st.column_config.NumberColumn("Average Partnership Runs", format="%.2f"),
                            "Success Rate (%)": st.column_config.NumberColumn("Success Rate (%)", format="%.2f")
                        }
                    )
                    st.success(f"👑 **{crown['partnership']}** leads the {mode.lower()} battle.")
                    st.download_button(
                        "⬇️ Download Q24 Partnership Rankings",
                        table_df.to_csv(index=False),
                        file_name="Q24_batting_partnerships.csv",
                        mime="text/csv"
                    )


            elif choice.startswith("Q25:"):
                st.subheader("🚀 Career Trajectory Arena")
                st.caption(
                    "Six-quarter batting evolution • 3+ matches per quarter • active players only"
                )

                required = [
                    "player_name",
                    "2025-Q1 (Avg Runs/SR)",
                    "2025-Q2 (Avg Runs/SR)",
                    "2025-Q3 (Avg Runs/SR)",
                    "2025-Q4 (Avg Runs/SR)",
                    "2026-Q1 (Avg Runs/SR)",
                    "2026-Q2 (Avg Runs/SR)",
                    "career_phase",
                ]
                missing = [c for c in required if c not in df.columns]

                if missing:
                    st.error("Q25 result is missing required columns: " + ", ".join(missing))
                elif df.empty:
                    st.info("No players meet the Q25 criteria.")
                else:
                    df = df[required].copy()

                    phases = ["Career Ascending", "Career Stable", "Career Declining"]
                    counts = df["career_phase"].value_counts()
                    df["_phase_order"] = df["career_phase"].map({
                        "Career Ascending": 1,
                        "Career Stable": 2,
                        "Career Declining": 3
                    }).fillna(4)

                    phase_colors = {
                        "Career Ascending": "🟢",
                        "Career Stable": "🟡",
                        "Career Declining": "🔴"
                    }

                    if "q25_view" not in st.session_state:
                        st.session_state["q25_view"] = "🚀 Trajectory"

                    st.markdown("### 🎮 Choose Your View")
                    b1, b2, b3, b4 = st.columns(4)
                    views = [
                        ("🚀 Trajectory", "q25_trajectory"),
                        ("🏏 Run Evolution", "q25_runs"),
                        ("⚡ SR Evolution", "q25_sr"),
                        ("🔎 Player Spotlight", "q25_spotlight"),
                    ]

                    for col, (label, key) in zip([b1, b2, b3, b4], views):
                        with col:
                            if st.button(label, key=key, width="stretch"):
                                st.session_state["q25_view"] = label
                                st.rerun()

                    st.markdown(
                        """
                        <style>
                        div[data-testid="stButton"] > button {
                            min-height: 48px;
                            border-radius: 12px;
                            font-weight: 700;
                            border: 1px solid rgba(255,255,255,0.20);
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )

                    ascending = int(counts.get("Career Ascending", 0))
                    stable = int(counts.get("Career Stable", 0))
                    declining = int(counts.get("Career Declining", 0))

                    leader = (
                        df[df["career_phase"] == "Career Ascending"].iloc[0]
                        if ascending
                        else df.iloc[0]
                    )

                    st.html(
                        f"""
                        <div style="
                            padding:28px;
                            border-radius:22px;
                            text-align:center;
                            margin:8px 0 20px 0;
                            border:1px solid rgba(255,215,0,0.35);
                            background:linear-gradient(
                                135deg,
                                rgba(255,215,0,0.16),
                                rgba(46,204,113,0.10),
                                rgba(52,152,219,0.08)
                            );
                        ">
                            <div style="font-size:48px;">👑</div>
                            <div style="
                                font-size:13px;
                                letter-spacing:3px;
                                opacity:.7;
                            ">CAREER TRAJECTORY LEADER</div>
                            <div style="
                                font-size:30px;
                                font-weight:800;
                                margin:8px 0;
                            ">{html.escape(str(leader["player_name"]))}</div>
                            <div style="font-size:18px;font-weight:700;">
                                {phase_colors.get(str(leader["career_phase"]), "🏏")}
                                {html.escape(str(leader["career_phase"]))}
                            </div>
                        </div>
                        """
                    )

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("🚀 Ascending", ascending)
                    with c2:
                        st.metric("🟡 Stable", stable)
                    with c3:
                        st.metric("🔻 Declining", declining)
                    with c4:
                        st.metric("👥 Players", len(df))

                    view = st.session_state["q25_view"]

                    if view == "🚀 Trajectory":
                        chart_df = counts.reindex(phases).fillna(0).reset_index()
                        chart_df.columns = ["phase", "players"]
                        fig = px.bar(
                            chart_df,
                            x="phase",
                            y="players",
                            color="phase",
                            text="players",
                            title="🏆 Career Phase Battle",
                            color_discrete_map={
                                "Career Ascending": "#2ecc71",
                                "Career Stable": "#f1c40f",
                                "Career Declining": "#e74c3c"
                            }
                        )
                        fig.update_layout(
                            height=430,
                            xaxis_title="Career Phase",
                            yaxis_title="Players",
                            showlegend=False
                        )
                        fig.update_traces(textposition="outside")
                        st.plotly_chart(fig, use_container_width=True)

                    elif view in ("🏏 Run Evolution", "⚡ SR Evolution"):
                        metric = "runs" if view == "🏏 Run Evolution" else "sr"
                        label = "Average Runs" if metric == "runs" else "Average Strike Rate"
                        quarter_cols = [
                            "2025-Q1 (Avg Runs/SR)",
                            "2025-Q2 (Avg Runs/SR)",
                            "2025-Q3 (Avg Runs/SR)",
                            "2025-Q4 (Avg Runs/SR)",
                            "2026-Q1 (Avg Runs/SR)",
                            "2026-Q2 (Avg Runs/SR)"
                        ]

                        selected = st.selectbox(
                            "Select player",
                            df["player_name"].tolist(),
                            key="q25_evolution_player"
                        )
                        row = df[df["player_name"] == selected].iloc[0]

                        values = []
                        for q in quarter_cols:
                            value = str(row[q])
                            try:
                                parts = value.split(" / ")
                                values.append(
                                    float(parts[0] if metric == "runs" else parts[1])
                                )
                            except (ValueError, IndexError):
                                values.append(None)

                        chart_df = pd.DataFrame({
                            "quarter": [q.split(" ")[0] for q in quarter_cols],
                            label: values
                        })

                        fig = px.line(
                            chart_df,
                            x="quarter",
                            y=label,
                            markers=True,
                            title=f"📈 {selected} — {label} Evolution"
                        )
                        fig.update_layout(
                            height=430,
                            xaxis_title="Quarter",
                            yaxis_title=label
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.success(
                            f"{phase_colors.get(str(row['career_phase']), '🏏')} "
                            f"**{selected}** — {row['career_phase']}"
                        )

                    else:
                        selected = st.selectbox(
                            "Choose a player",
                            df["player_name"].tolist(),
                            key="q25_spotlight_player"
                        )
                        row = df[df["player_name"] == selected].iloc[0]

                        st.markdown("### 🔎 Performance Spotlight")
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric(
                                "Career Phase",
                                str(row["career_phase"]).replace("Career ", "")
                            )
                        with m2:
                            st.metric("Latest Quarter", str(row["2026-Q2 (Avg Runs/SR)"]))
                        with m3:
                            st.metric("Starting Quarter", str(row["2025-Q1 (Avg Runs/SR)"]))

                        quarter_cols = [
                            "2025-Q1 (Avg Runs/SR)",
                            "2025-Q2 (Avg Runs/SR)",
                            "2025-Q3 (Avg Runs/SR)",
                            "2025-Q4 (Avg Runs/SR)",
                            "2026-Q1 (Avg Runs/SR)",
                            "2026-Q2 (Avg Runs/SR)"
                        ]
                        rows = []
                        for q in quarter_cols:
                            value = str(row[q])
                            try:
                                runs, sr = value.split(" / ")
                                rows.append({
                                    "Quarter": q.split(" ")[0],
                                    "Avg Runs": float(runs),
                                    "Avg Strike Rate": float(sr)
                                })
                            except (ValueError, IndexError):
                                rows.append({
                                    "Quarter": q.split(" ")[0],
                                    "Avg Runs": None,
                                    "Avg Strike Rate": None
                                })

                        chart_df = pd.DataFrame(rows)
                        fig = px.line(
                            chart_df,
                            x="Quarter",
                            y=["Avg Runs", "Avg Strike Rate"],
                            markers=True,
                            title=f"📊 {selected} — Six-Quarter Profile"
                        )
                        fig.update_layout(height=430)
                        st.plotly_chart(fig, use_container_width=True)

                    st.divider()
                    st.markdown("### 📋 Career Trajectory Rankings")

                    table_df = df.sort_values(
                        ["_phase_order", "player_name"]
                    ).drop(columns="_phase_order").copy()

                    table_df.columns = [
                        "Player",
                        "2025-Q1 (Avg Runs/SR)",
                        "2025-Q2 (Avg Runs/SR)",
                        "2025-Q3 (Avg Runs/SR)",
                        "2025-Q4 (Avg Runs/SR)",
                        "2026-Q1 (Avg Runs/SR)",
                        "2026-Q2 (Avg Runs/SR)",
                        "Career Phase"
                    ]

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        height=520
                    )

                    st.download_button(
                        "⬇️ Download Q25 Career Trajectory",
                        table_df.to_csv(index=False),
                        file_name="Q25_career_trajectory.csv",
                        mime="text/csv"
                    )

            else:

                st.dataframe(
                    df,
                    use_container_width=True
                )

                st.download_button(
                    "Download results as CSV",
                    df.to_csv(index=False),
                    file_name=(
                        f"{choice.split(':')[0].strip()}.csv"
                    )
                )


        except Exception as e:

            st.error(
                f"Query failed: {e}"
            )

st.divider()

st.subheader(
    "Or write your own query"
)

custom_sql = st.text_area(
    "Custom SQL (SELECT only)",
    height=120
)


if st.button("Run custom query"):

    if not custom_sql.strip().lower().startswith(
        "select"
    ):

        st.error(
            "Only SELECT statements are allowed here."
        )

    else:

        try:

            df = run_query(
                custom_sql
            )

            st.dataframe(
                df,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Query failed: {e}"
            )