import sys
import json
import time
from pathlib import Path

import pandas as pd
import textwrap
import streamlit as st

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.db_connection import run_query
from utils.api_helper import (
    get_top_player_leaderboard,
    get_live_matches,
    get_icc_team_rankings,
    get_top_player_stats,
)
from utils.gamification import (
    init_game_state,
    add_xp,
    complete_mission,
)
from utils.theme import apply_theme


# Page configuration

st.set_page_config(
    page_title="Cricket Intelligence Hub | Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
)


# Page navigation and section state

SECTION_CONFIG = {
    "🏆 Teams": {
        "key": "teams",
        "title": "Team Rankings & Standings",
        "subtitle": "Explore ICC team rankings, rating power and competitive strength.",
        "badge": "🏆 TEAM INTELLIGENCE • CRICKET ANALYTICS ARENA",
        "tagline": "🏆 TEAM RANKINGS &nbsp; • &nbsp; 📊 STANDINGS &nbsp; • &nbsp; 🔥 TEAM STRENGTH",
    },
    "⭐ Top Players": {
        "key": "players",
        "title": "Top Player Rankings",
        "subtitle": "Compare elite batsmen and bowlers across ODI, Test and T20 formats.",
        "badge": "⭐ PLAYER RANKINGS • CRICKET ANALYTICS ARENA",
        "tagline": "⭐ ICC RANKINGS &nbsp; • &nbsp; 🏏 BATTING &nbsp; • &nbsp; 🎯 BOWLING",
    },
    "🎮 Fantasy Cricket": {
        "key": "fantasy",
        "title": "Fantasy Cricket Arena",
        "subtitle": "",
        "badge": "🎮 FANTASY CRICKET • CRICKET ANALYTICS ARENA",
        "tagline": "📈 PLAYER FORM &nbsp; • &nbsp; 🤝 HEAD-TO-HEAD &nbsp; • &nbsp; 🔴 LIVE SCORES",
    },
}

st.session_state.setdefault("analytics_section", "🏆 Teams")

selected_section = st.segmented_control(
    "Analytics section",
    list(SECTION_CONFIG.keys()),
    default=st.session_state["analytics_section"],
    key="analytics_section",
    label_visibility="collapsed",
)

if selected_section is None:
    selected_section = "🏆 Teams"

section = SECTION_CONFIG[selected_section]


# Sidebar team preview helper

def _sidebar_team_preview(format_code="odi"):
    """Return the top five ranked teams for the sidebar."""
    try:
        data = get_icc_team_rankings(format_code)

        def walk(value):
            if isinstance(value, list):
                if value and all(isinstance(item, dict) for item in value):
                    keys = set().union(*(item.keys() for item in value))
                    if (
                        keys & {"name", "team", "teamName", "country"}
                        and keys & {"rank", "position", "ranking", "rating", "points"}
                    ):
                        return value
                for item in value:
                    found = walk(item)
                    if found:
                        return found

            if isinstance(value, dict):
                preferred = [
                    "rank",
                    "ranks",
                    "ranking",
                    "rankings",
                    "teamRankings",
                    "rankingData",
                    "data",
                    "content",
                    "list",
                    "items",
                ]
                for key in preferred:
                    if key in value:
                        found = walk(value[key])
                        if found:
                            return found
                for child in value.values():
                    found = walk(child)
                    if found:
                        return found

            return []

        rows = []
        for index, record in enumerate(walk(data), start=1):
            if not isinstance(record, dict):
                continue

            team = (
                record.get("name")
                or record.get("teamName")
                or record.get("team")
                or record.get("country")
            )
            if isinstance(team, dict):
                team = (
                    team.get("name")
                    or team.get("teamName")
                    or team.get("shortName")
                )

            if not team:
                continue

            rank = record.get("rank") or record.get("position") or record.get("ranking") or index
            rating = record.get("rating") or record.get("points") or 0

            rows.append(
                {
                    "Rank": _safe_int_sidebar(rank, index),
                    "Team": str(team),
                    "Rating": _safe_int_sidebar(rating, 0),
                }
            )

        if rows:
            return (
                pd.DataFrame(rows)
                .drop_duplicates(subset=["Team"], keep="first")
                .sort_values("Rank")
                .head(5)
                .reset_index(drop=True)
            )
    except Exception:
        pass

    try:
        return run_query(
            """
            SELECT
                position AS Rank,
                team AS Team,
                rating AS Rating
            FROM icc_rankings_teams
            WHERE LOWER(format) = LOWER(?)
            ORDER BY position
            LIMIT 5
            """,
            (format_code,),
        )
    except Exception:
        return pd.DataFrame(columns=["Rank", "Team", "Rating"])


def _safe_int_sidebar(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _sidebar_player_preview(format_code="odi", ranking_type="batting"):
    """Return the top five ICC-ranked players for the sidebar."""
    table_map = {
        "odi": "icc_rankings_odi",
        "test": "icc_rankings_test",
        "t20": "icc_rankings_t20",
    }
    table = table_map.get(str(format_code).lower().strip())
    if not table:
        return pd.DataFrame(columns=["Rank", "Player", "Team", "Rating"])

    type_map = {
        "batting": "batting",
        "bowling": "bowling",
    }
    ranking_type = type_map.get(ranking_type, "batting")

    try:
        df = run_query(
            f"""
            SELECT
                RANK() OVER (ORDER BY rating DESC, player ASC) AS Rank,
                player AS Player,
                team AS Team,
                rating AS Rating
            FROM {table}
            WHERE LOWER(TRIM(ranking_type)) = LOWER(TRIM(?))
              AND player IS NOT NULL
              AND TRIM(player) <> ''
              AND rating IS NOT NULL
              AND rating > 0
            ORDER BY rating DESC, player ASC
            LIMIT 5
            """,
            (ranking_type,),
        )

        if not df.empty:
            df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce").fillna(0).astype(int)
            df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(0)
            return df

    except Exception:
        pass

    return pd.DataFrame(columns=["Rank", "Player", "Team", "Rating"])


# Sidebar navigation

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

    /* Native segmented control used as the section switcher. */
    [data-testid="stSegmentedControl"] {
        margin-bottom: 8px !important;
    }

    [data-testid="stSegmentedControl"] button {
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if section["key"] == "teams":
    # Keep the sidebar synchronized with the selected ICC format.
    sidebar_format = st.session_state.get("team_ranking_format", "odi")
    if sidebar_format not in {"odi", "test", "t20"}:
        sidebar_format = "odi"

    sidebar_teams = _sidebar_team_preview(sidebar_format)

    with st.sidebar.container(border=True):
        st.markdown("🏆 **TOP 5 TEAMS**")
        st.caption(f"Current ICC {sidebar_format.upper()} ranking")

        if sidebar_teams.empty:
            st.caption("Team rankings are temporarily unavailable.")
        else:
            for _, team in sidebar_teams.iterrows():
                rank = _safe_int_sidebar(team.get("Rank"), 0)
                team_name = str(team.get("Team", "Unknown"))
                rating = _safe_int_sidebar(team.get("Rating"), 0)

                if rank == 1:
                    icon = "👑"
                elif rank == 2:
                    icon = "🥈"
                elif rank == 3:
                    icon = "🥉"
                else:
                    icon = "🏏"

                team_cols = st.columns([0.38, 1.72, 0.65])
                with team_cols[0]:
                    st.markdown(f"**{icon}**")
                with team_cols[1]:
                    st.markdown(f"**{team_name}**")
                with team_cols[2]:
                    st.caption(f"{rating}")

elif section["key"] == "players":
    # Keep the player sidebar synchronized with the Top Players leaderboard.
    sidebar_format = st.session_state.get("player_ranking_format", "odi")
    if sidebar_format not in {"odi", "test", "t20"}:
        sidebar_format = "odi"

    sidebar_format_label = {
        "odi": "ODI",
        "test": "Test",
        "t20": "T20",
    }[sidebar_format]

    sidebar_cache_dir = PROJECT_ROOT / "data" / "api_cache"

    sidebar_batting_path = (
        sidebar_cache_dir
        / f"Top_15_Batters_{sidebar_format_label}.json"
    )
    sidebar_bowling_path = (
        sidebar_cache_dir
        / f"Top_15_Bowlers_{sidebar_format_label}.json"
    )

    def _load_sidebar_top_5(path, role):
        """Load the current Top 5 from the combined ranking JSON."""
        if not path.is_file():
            return []

        def _sidebar_number(value, default=0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return []

        players = payload.get("players", [])

        if not isinstance(players, list):
            return []

        result = []

        for player in players[:5]:
            if not isinstance(player, dict):
                continue

            name = str(
                player.get("player", "")
            ).strip()

            if not name:
                continue

            rank = _safe_int_sidebar(
                player.get("rank"),
                len(result) + 1,
            )

            if role == "batting":
                result.append(
                    {
                        "rank": rank,
                        "name": name,
                        "primary": _safe_int_sidebar(
                            player.get("runs"),
                            0,
                        ),
                        "secondary": _sidebar_number(
                            player.get("strike_rate"),
                            0,
                        ),
                        "secondary_label": "SR",
                    }
                )
            else:
                result.append(
                    {
                        "rank": rank,
                        "name": name,
                        "primary": _safe_int_sidebar(
                            player.get("wickets"),
                            0,
                        ),
                        "secondary": _sidebar_number(
                            player.get("economy"),
                            0,
                        ),
                        "secondary_label": "ECO",
                    }
                )

        return result

    sidebar_batsmen = _load_sidebar_top_5(
        sidebar_batting_path,
        "batting",
    )
    sidebar_bowlers = _load_sidebar_top_5(
        sidebar_bowling_path,
        "bowling",
    )

    with st.sidebar.container(border=True):
        st.markdown("⭐ **TOP PLAYER STATS**")
        st.caption(
            f"Current Top 15 leaderboard • {sidebar_format_label}"
        )

        # Top five batters from the same JSON used by the main leaderboard.
        with st.container(border=True):
            st.markdown("🏏 **TOP 5 BATTERS**")

            if not sidebar_batsmen:
                st.caption(
                    "Batting rankings are temporarily unavailable."
                )
            else:
                for player in sidebar_batsmen:
                    rank = player["rank"]

                    if rank == 1:
                        icon = "👑"
                    elif rank == 2:
                        icon = "🥈"
                    elif rank == 3:
                        icon = "🥉"
                    else:
                        icon = "🏏"

                    player_cols = st.columns(
                        [0.36, 1.70, 0.70]
                    )

                    with player_cols[0]:
                        st.markdown(
                            f"**{icon} #{rank}**"
                        )

                    with player_cols[1]:
                        st.markdown(
                            f"**{player['name']}**"
                        )

                    with player_cols[2]:
                        st.markdown(
                            f"**{player['primary']:,}**"
                        )
                        st.caption(
                            f"{player['secondary']:.2f} SR"
                        )

        # Top five bowlers from the same JSON used by the main leaderboard.
        with st.container(border=True):
            st.markdown("🎯 **TOP 5 BOWLERS**")

            if not sidebar_bowlers:
                st.caption(
                    "Bowling rankings are temporarily unavailable."
                )
            else:
                for player in sidebar_bowlers:
                    rank = player["rank"]

                    if rank == 1:
                        icon = "👑"
                    elif rank == 2:
                        icon = "🥈"
                    elif rank == 3:
                        icon = "🥉"
                    else:
                        icon = "🎯"

                    player_cols = st.columns(
                        [0.36, 1.70, 0.70]
                    )

                    with player_cols[0]:
                        st.markdown(
                            f"**{icon} #{rank}**"
                        )

                    with player_cols[1]:
                        st.markdown(
                            f"**{player['name']}**"
                        )

                    with player_cols[2]:
                        st.markdown(
                            f"**{player['primary']:,}**"
                        )
                        st.caption(
                            f"{player['secondary']:.2f} ECO"
                        )



# Application state

init_game_state()

apply_theme(
    badge_text=section["badge"],
    title=section["title"],
    subtitle=section["subtitle"],
    tagline=section["tagline"],
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

    .fantasy-scout-panel {
        position: sticky;
        top: 12px;
    }

    /* Compact, but still readable Fantasy Scout Checklist cards. */
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        padding: 0.42rem 0.62rem !important;
        min-height: 0 !important;
        margin-bottom: 0.25rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] p {
        font-size: 0.84rem !important;
        line-height: 1.15 !important;
        margin: 0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.55rem 0.62rem !important;
        margin-bottom: 0.45rem !important;
    }

    /* Separate nested ranking cards inside the Top ICC Players card. */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.48rem 0.52rem !important;
        margin: 0.35rem 0 0.35rem 0 !important;
        border-color: rgba(255,255,255,0.12) !important;
        background: rgba(255,255,255,0.018) !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
        margin-bottom: 0.18rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
        font-size: 0.72rem !important;
        line-height: 1.2 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main page state

st.session_state.setdefault("favorite_players", set())
st.session_state.setdefault("top_stats_formats_seen", set())
st.session_state.setdefault("top_stats_formats_bonus_awarded", False)


def render_favorite_picker(category, fmt, players):
    """Render a compact favorite-player control for an ICC ranking list."""
    if not players:
        return

    favorite_key = f"favorite_{category}_{fmt}"
    selected = st.selectbox(
        "⭐ Favorite player",
        players,
        key=favorite_key,
        label_visibility="collapsed",
    )

    if st.button(
        "⭐ Add to Favorites",
        key=f"add_favorite_{category}_{fmt}",
        use_container_width=True,
    ):
        st.session_state["favorite_players"].add(selected)
        st.toast(f"⭐ {selected} added to favorites.", icon="⭐")


# Data helpers

def _safe_number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _flatten_dicts(value):
    """Return dictionaries found recursively in a Cricbuzz response."""
    found = []

    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_flatten_dicts(child))

    elif isinstance(value, list):
        for child in value:
            found.extend(_flatten_dicts(child))

    return found


def _find_team_ranking_entries(value):
    """Find Cricbuzz team ranking records."""
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            keys = set().union(*(item.keys() for item in value))

            if keys & {"name", "team", "teamName", "country"} and keys & {
                "rank",
                "rating",
                "points",
                "matches",
            }:
                return value

        for item in value:
            found = _find_team_ranking_entries(item)
            if found:
                return found

    elif isinstance(value, dict):
        for key in [
            "rank",
            "ranks",
            "ranking",
            "rankings",
            "teamRankings",
            "rankingData",
            "data",
            "content",
            "list",
            "items",
        ]:
            if key in value:
                found = _find_team_ranking_entries(value[key])
                if found:
                    return found

        for child in value.values():
            found = _find_team_ranking_entries(child)
            if found:
                return found

    return []


def _normalize_team_rankings(data):
    """Normalize Cricbuzz team ranking records."""
    entries = _find_team_ranking_entries(data)
    rows = []

    for index, record in enumerate(entries, start=1):
        if not isinstance(record, dict):
            continue

        team = (
            record.get("name")
            or record.get("teamName")
            or record.get("team")
            or record.get("country")
        )

        if isinstance(team, dict):
            team = (
                team.get("name")
                or team.get("teamName")
                or team.get("shortName")
            )

        if not team:
            continue

        rows.append(
            {
                "Rank": _safe_int(
                    record.get("rank")
                    or record.get("position")
                    or record.get("ranking"),
                    index,
                ),
                "Team": str(team),
                "Rating": _safe_number(record.get("rating")),
                "Matches": _safe_int(record.get("matches")),
                "Points": _safe_number(record.get("points")),
                "Last Updated": record.get("lastUpdatedOn", ""),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "Rank",
                "Team",
                "Rating",
                "Matches",
                "Points",
                "Last Updated",
            ]
        )

    return (
        pd.DataFrame(rows)
        .drop_duplicates(subset=["Team"], keep="first")
        .sort_values(["Rank", "Team"])
        .reset_index(drop=True)
    )


def _find_match_rows(team1, team2, years=3):
    """Return recent head-to-head matches for two teams."""
    query = """
        SELECT
            match_date,
            team1,
            team2,
            winner,
            match_type,
            venue_id
        FROM matches
        WHERE (
            (LOWER(team1) = LOWER(?) AND LOWER(team2) = LOWER(?))
            OR
            (LOWER(team1) = LOWER(?) AND LOWER(team2) = LOWER(?))
        )
        AND match_date IS NOT NULL
        AND date(match_date) >= date('now', ?)
        ORDER BY date(match_date) DESC
    """

    try:
        return run_query(
            query,
            (
                team1,
                team2,
                team2,
                team1,
                f"-{int(years * 365)} days",
            ),
        )
    except Exception:
        return pd.DataFrame()


def _find_player_form(player_name):
    """Return recent batting innings across all available formats."""
    try:
        # Resolve the visible real name to the authoritative active player.
        player_lookup = run_query(
            """
            SELECT player_id, player_name, real_name, country
            FROM players
            WHERE admin_active = 1
              AND (
                    LOWER(TRIM(player_name)) = LOWER(TRIM(?))
                    OR LOWER(TRIM(COALESCE(real_name, ''))) = LOWER(TRIM(?))
                  )
            ORDER BY
                CASE
                    WHEN LOWER(TRIM(COALESCE(real_name, ''))) =
                         LOWER(TRIM(?))
                    THEN 0
                    ELSE 1
                END,
                player_name
            LIMIT 1
            """,
            (player_name, player_name, player_name),
        )

        if player_lookup.empty:
            return pd.DataFrame()

        player_id = int(player_lookup.iloc[0]["player_id"])
        db_player_name = str(
            player_lookup.iloc[0]["player_name"] or player_name
        ).strip()
        real_name = str(
            player_lookup.iloc[0]["real_name"] or ""
        ).strip()
        country = str(
            player_lookup.iloc[0]["country"] or ""
        ).strip()

        # innings_scores is the primary source and already connects each
        # innings to its match. No format filter is applied here.
        query = """
            SELECT
                ? AS Player,
                i.match_date AS Match_Date,
                CASE
                    WHEN LOWER(TRIM(COALESCE(m.match_type, ''))) IN ('t20', 't20i', 'it20')
                        THEN 'T20'
                    WHEN LOWER(TRIM(COALESCE(m.match_type, ''))) = 'odi'
                        THEN 'ODI'
                    WHEN LOWER(TRIM(COALESCE(m.match_type, ''))) = 'test'
                        THEN 'TEST'
                    ELSE UPPER(TRIM(COALESCE(m.match_type, 'Unknown')))
                END AS Format,
                i.runs_scored AS Runs,
                i.balls_faced AS Balls,
                i.fours AS Fours,
                i.sixes AS Sixes,
                i.strike_rate AS Strike_Rate,
                CASE
                    WHEN LOWER(TRIM(m.team1)) = LOWER(TRIM(?))
                    THEN m.team2
                    WHEN LOWER(TRIM(m.team2)) = LOWER(TRIM(?))
                    THEN m.team1
                    WHEN LOWER(TRIM(m.team1)) = LOWER(TRIM(?))
                    THEN m.team2
                    WHEN LOWER(TRIM(m.team2)) = LOWER(TRIM(?))
                    THEN m.team1
                    ELSE COALESCE(m.description, 'Unknown')
                END AS Opposition,
                COALESCE(v.venue_name, 'Unknown') AS Ground
            FROM innings_scores AS i
            INNER JOIN matches AS m
                ON m.match_id = i.match_id
            LEFT JOIN venues AS v
                ON v.venue_id = m.venue_id
            WHERE i.player_id = ?
              AND i.match_date IS NOT NULL
            ORDER BY date(i.match_date) DESC, i.id DESC
            LIMIT 10
        """

        params = (
            real_name or db_player_name,
            db_player_name,
            db_player_name,
            country,
            country,
            player_id,
        )

        form_df = run_query(query, params)

        # Q23 is a fallback for imported innings not represented in
        # innings_scores. It also returns the format so the combined board
        # remains format-aware without requiring a filter.
        if form_df.empty:
            q23_query = """
                SELECT
                    COALESCE(
                        NULLIF(TRIM(real_name), ''),
                        NULLIF(TRIM(player_name), ''),
                        ?
                    ) AS Player,
                    match_date AS Match_Date,
                    CASE
                        WHEN LOWER(TRIM(COALESCE(format, ''))) IN ('t20', 't20i', 'it20')
                            THEN 'T20'
                        WHEN LOWER(TRIM(COALESCE(format, ''))) = 'odi'
                            THEN 'ODI'
                        WHEN LOWER(TRIM(COALESCE(format, ''))) = 'test'
                            THEN 'TEST'
                        ELSE UPPER(TRIM(COALESCE(format, 'Unknown')))
                    END AS Format,
                    runs_scored AS Runs,
                    balls_faced AS Balls,
                    fours AS Fours,
                    sixes AS Sixes,
                    strike_rate AS Strike_Rate,
                    COALESCE(opposition, 'Unknown') AS Opposition,
                    COALESCE(ground, 'Unknown') AS Ground
                FROM Q23_batting_innings_SR
                WHERE player_id = ?
                ORDER BY date(match_date) DESC, id DESC
                LIMIT 10
            """

            form_df = run_query(
                q23_query,
                (real_name or db_player_name, player_id),
            )

        return form_df

    except Exception as exc:
        print(
            f"Fantasy Player Form lookup failed for "
            f"{player_name}: {exc}"
        )
        return pd.DataFrame()

def _current_player_names():
    """Return real names for active players only."""
    try:
        df = run_query(
            """
            SELECT DISTINCT
                COALESCE(
                    NULLIF(TRIM(real_name), ''),
                    NULLIF(TRIM(player_name), '')
                ) AS player_name
            FROM players
            WHERE admin_active = 1
              AND COALESCE(
                    NULLIF(TRIM(real_name), ''),
                    NULLIF(TRIM(player_name), '')
                  ) IS NOT NULL
              AND TRIM(
                    COALESCE(
                        NULLIF(TRIM(real_name), ''),
                        NULLIF(TRIM(player_name), '')
                    )
                  ) <> ''
            ORDER BY player_name
            """
        )

        if not df.empty:
            return (
                df["player_name"]
                .dropna()
                .astype(str)
                .str.strip()
                .drop_duplicates()
                .tolist()
            )
    except Exception:
        pass

    return []


def _normalize_live_matches(data):
    """Extract compact live match records from Cricbuzz data."""
    rows = []

    for record in _flatten_dicts(data):
        team1 = (
            record.get("team1")
            or record.get("team1Name")
        )
        team2 = (
            record.get("team2")
            or record.get("team2Name")
        )

        if isinstance(team1, dict):
            team1 = (
                team1.get("teamName")
                or team1.get("name")
            )

        if isinstance(team2, dict):
            team2 = (
                team2.get("teamName")
                or team2.get("name")
            )

        if not team1 or not team2:
            continue

        rows.append(
            {
                "Teams": f"{team1} vs {team2}",
                "Status": (
                    record.get("status")
                    or record.get("matchStatus")
                    or record.get("state")
                    or "Live"
                ),
                "Score": (
                    record.get("score")
                    or record.get("status")
                    or ""
                ),
            }
        )

    return pd.DataFrame(rows).drop_duplicates()


# ICC player ranking helpers

def _find_ranking_entries(value, ranking_type):
    """Find player ranking entries inside common Cricbuzz response structures."""
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            keys = set().union(*(item.keys() for item in value))
            player_keys = {
                "player",
                "playerName",
                "name",
                "fullName",
                "batsman",
                "bowler",
                "playerDetails",
            }
            rating_keys = {
                "rating",
                "points",
                "ratingPoints",
                "currentRating",
                "rankRating",
                "rankingRating",
            }

            if keys & player_keys and keys & rating_keys:
                return value

        for item in value:
            found = _find_ranking_entries(
                item,
                ranking_type,
            )
            if found:
                return found

    elif isinstance(value, dict):
        preferred_keys = [
            ranking_type,
            f"{ranking_type}s",
            "rankings",
            "ranking",
            "rankingsList",
            "rankingList",
            "rankingData",
            "data",
            "content",
            "list",
            "items",
        ]

        for key in preferred_keys:
            if key in value:
                found = _find_ranking_entries(
                    value[key],
                    ranking_type,
                )
                if found:
                    return found

        for child in value.values():
            found = _find_ranking_entries(
                child,
                ranking_type,
            )
            if found:
                return found

    return []


def _first_value(record, keys, default=None):
    for key in keys:
        if key in record and record[key] not in (None, ""):
            value = record[key]

            if isinstance(value, dict):
                nested = _first_value(
                    value,
                    [
                        "name",
                        "fullName",
                        "playerName",
                        "shortName",
                    ],
                    default,
                )

                if nested not in (None, ""):
                    return nested

            return value

    return default


def _normalize_ranking_entries(entries):
    """Normalize Cricbuzz player ranking records."""
    normalized = []

    for index, record in enumerate(entries, start=1):
        if not isinstance(record, dict):
            continue

        player_obj = record.get("playerDetails")

        if not isinstance(player_obj, dict):
            player_obj = (
                record.get("player")
                if isinstance(
                    record.get("player"),
                    dict,
                )
                else {}
            )

        player = _first_value(
            record,
            [
                "playerName",
                "name",
                "fullName",
                "player",
            ],
            None,
        )

        if isinstance(player, dict):
            player = _first_value(
                player,
                [
                    "name",
                    "fullName",
                    "playerName",
                ],
                None,
            )

        if not player and player_obj:
            player = _first_value(
                player_obj,
                [
                    "name",
                    "fullName",
                    "playerName",
                    "shortName",
                ],
                None,
            )

        team = _first_value(
            record,
            [
                "team",
                "country",
                "teamName",
                "countryName",
            ],
            None,
        )

        if isinstance(team, dict):
            team = _first_value(
                team,
                [
                    "name",
                    "teamName",
                    "shortName",
                ],
                None,
            )

        if not team and player_obj:
            team = _first_value(
                player_obj,
                [
                    "team",
                    "country",
                    "teamName",
                    "countryName",
                ],
                None,
            )

        rating = _first_value(
            record,
            [
                "rating",
                "points",
                "ratingPoints",
                "currentRating",
                "rankRating",
                "rankingRating",
            ],
            None,
        )

        career_best = _first_value(
            record,
            [
                "careerBestRating",
                "career_best_rating",
                "careerBest",
                "bestRating",
                "best",
            ],
            None,
        )

        rank = _first_value(
            record,
            [
                "rank",
                "ranking",
                "position",
            ],
            index,
        )

        if player is None:
            continue

        normalized.append(
            {
                "Rank": rank,
                "Player": str(player),
                "Country": (
                    str(team)
                    if team is not None
                    else "Unknown"
                ),
                "Rating": rating,
                "Career_Best_Rating": career_best,
            }
        )

    if not normalized:
        return pd.DataFrame(
            columns=[
                "Rank",
                "Player",
                "Country",
                "Rating",
                "Career_Best_Rating",
            ]
        )

    df = pd.DataFrame(normalized)

    df["Rating"] = pd.to_numeric(
        df["Rating"],
        errors="coerce",
    )

    df["Career_Best_Rating"] = pd.to_numeric(
        df["Career_Best_Rating"],
        errors="coerce",
    )

    df = (
        df.drop_duplicates(
            subset=["Player"],
            keep="first",
        )
        .sort_values(
            ["Rating", "Player"],
            ascending=[False, True],
            na_position="last",
        )
        .reset_index(drop=True)
    )

    df["Rank"] = range(1, len(df) + 1)

    return df


def get_icc_rankings(format_code, ranking_type):
    """Load player rankings from cache/API first, SQLite as fallback."""
    try:
        api_data = get_top_player_leaderboard(
            format_code
        )

        entries = _find_ranking_entries(
            api_data,
            ranking_type,
        )

        df = _normalize_ranking_entries(
            entries
        )

        if not df.empty:
            return df.head(20)

    except Exception:
        pass

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

    return run_query(
        query,
        (ranking_type,),
    )


def render_icc_leaderboard(df, category, fmt):
    """Render a compact gamified ICC top-20 leaderboard."""
    if df.empty:
        st.warning(
            f"No ICC {category} rankings found for "
            f"{fmt.upper()}."
        )
        return

    df = df.copy()

    for column in [
        "Rank",
        "Rating",
        "Career_Best_Rating",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df["Rank"] = (
        df["Rank"]
        .fillna(0)
        .astype(int)
    )
    df["Rating"] = (
        df["Rating"]
        .fillna(0)
    )
    df["Career_Best_Rating"] = (
        df["Career_Best_Rating"]
        .fillna(0)
    )

    max_rating = max(
        float(df["Rating"].max()),
        1.0,
    )

    category_icon = (
        "🏏"
        if category == "batsmen"
        else "🎯"
    )

    category_label = (
        "ICC BATTING RANKINGS"
        if category == "batsmen"
        else "ICC BOWLING RANKINGS"
    )

    st.markdown(
        f"### {category_icon} ICC Top 20 "
        f"{category.title()}"
    )

    st.caption(
        f"🏆 {category_label} • "
        f"{len(df)} players • {fmt.upper()} • "
        "Ranked by ICC rating"
    )

    header_cols = st.columns(
        [
            0.72,
            2.00,
            1.35,
            0.90,
            1.10,
            1.55,
            0.90,
        ]
    )

    for column, header in zip(
        header_cols,
        [
            "RANK",
            "PLAYER",
            "TEAM",
            "RATING",
            "CAREER BEST",
            "RATING POWER",
            "STATUS",
        ],
    ):
        column.caption(header)

    for _, player in df.iterrows():
        rank = int(player["Rank"])
        player_name = str(
            player.get(
                "Player",
                "Unknown",
            )
        )
        country = str(
            player.get(
                "Country",
                "Unknown",
            )
        )
        rating = float(
            player.get(
                "Rating",
                0,
            )
            or 0
        )
        career_best = float(
            player.get(
                "Career_Best_Rating",
                0,
            )
            or 0
        )

        power = min(
            max(
                rating / max_rating,
                0.0,
            ),
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
                [
                    0.72,
                    2.00,
                    1.35,
                    0.90,
                    1.10,
                    1.55,
                    0.90,
                ]
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
                    f"**{career_best:,.0f}**"
                )

            with row_cols[5]:
                st.caption(
                    f"Rating Power • "
                    f"{power * 100:.0f}%"
                )
                st.progress(
                    power,
                    text=None,
                )

            with row_cols[6]:
                st.markdown("**ICC**")
                st.caption("Ranked")


# Section content

# Teams section

if section["key"] == "teams":
        st.markdown("### 🏆 ICC Team Standings")

        st.caption(
            "Explore team strength, rating power and ranking position across formats."
        )

        team_format = st.selectbox(
            "Team ranking format",
            ["odi", "test", "t20"],
            format_func=lambda x: x.upper(),
            key="team_ranking_format",
        )

        try:
            team_ranking_data = get_icc_team_rankings(team_format)
            team_df = _normalize_team_rankings(team_ranking_data)
        except Exception:
            team_df = pd.DataFrame()

        if team_df.empty:
            try:
                team_df = run_query(
                    """
                    SELECT
                        position AS Rank,
                        team AS Team,
                        rating AS Rating,
                        matches AS Matches,
                        points AS Points,
                        imported_at AS "Last Updated"
                    FROM icc_rankings_teams
                    WHERE LOWER(format) = LOWER(?)
                    ORDER BY position
                    """,
                    (team_format,),
                )
            except Exception:
                team_df = pd.DataFrame()

        if team_df.empty:
            st.info("No ICC team standings are available.")
        else:
            team_df = team_df.copy()

            for column in ["Rank", "Rating", "Matches", "Points"]:
                if column in team_df.columns:
                    team_df[column] = pd.to_numeric(
                        team_df[column],
                        errors="coerce",
                    )

            team_df["Rank"] = team_df["Rank"].fillna(0).astype(int)
            team_df["Rating"] = team_df["Rating"].fillna(0)
            team_df["Matches"] = team_df["Matches"].fillna(0).astype(int)
            team_df["Points"] = team_df["Points"].fillna(0)

            st.markdown("#### 🏆 Team Leaderboard")

            max_rating = max(float(team_df["Rating"].max()), 1.0)
            leaderboard_df = team_df.head(20)

            header_cols = st.columns(
                [0.60, 2.00, 0.90, 1.10, 1.10, 1.65, 1.00]
            )

            for column, header in zip(
                header_cols,
                [
                    "RANK",
                    "TEAM",
                    "RATING",
                    "MATCHES",
                    "POINTS",
                    "RATING POWER",
                    "STATUS",
                ],
            ):
                column.caption(header)

            for _, team in leaderboard_df.iterrows():
                rank = int(team["Rank"])
                team_name = str(team["Team"])
                rating = float(team["Rating"])
                matches = int(team["Matches"])
                points = float(team["Points"])

                power = min(max(rating / max_rating, 0.0), 1.0)

                if rank == 1:
                    rank_display = "👑 #1"
                    badge = "LEGEND"
                    status = "👑 CHAMPION"
                elif rank == 2:
                    rank_display = "🥈 #2"
                    badge = "ELITE"
                    status = "💎 ELITE"
                elif rank == 3:
                    rank_display = "🥉 #3"
                    badge = "ELITE"
                    status = "💎 ELITE"
                elif rank <= 5:
                    rank_display = f"🔥 #{rank}"
                    badge = "TOP 5"
                    status = "🔥 HOT"
                elif rank <= 10:
                    rank_display = f"⚡ #{rank}"
                    badge = "TOP 10"
                    status = "⚡ CONTENDER"
                else:
                    rank_display = f"🏅 #{rank}"
                    badge = "TOP 20+"
                    status = "🎯 CHALLENGER"

                with st.container(border=True):
                    row_cols = st.columns(
                        [0.60, 2.00, 0.90, 1.10, 1.10, 1.65, 1.00]
                    )

                    with row_cols[0]:
                        st.markdown(f"**{rank_display}**")
                        st.caption(badge)

                    with row_cols[1]:
                        st.markdown(f"**{team_name}**")

                    with row_cols[2]:
                        st.markdown(f"**{rating:,.0f}**")

                    with row_cols[3]:
                        st.write(f"{matches:,}")

                    with row_cols[4]:
                        st.markdown(f"**{points:,.0f}**")

                    with row_cols[5]:
                        st.caption(f"{power * 100:.0f}% POWER")
                        st.progress(power, text=None)

                    with row_cols[6]:
                        st.markdown(f"**{status}**")

            st.caption(
                f"Top {len(leaderboard_df)} of {len(team_df)} ranked teams • "
                f"{team_format.upper()} • ICC rating-based standings"
            )



# Top Player Stats helpers

TOP_PLAYER_STAT_CONFIG = {
    "most_runs": {
        "title": "Runs (R)",
        "api_key": "most_runs",
        "value_label": "RUNS",
    },
    "batting_average": {
        "title": "Batting Average (Ave)",
        "api_key": "batting_average",
        "value_label": "AVE",
    },
    "strike_rate": {
        "title": "Strike Rate (SR)",
        "api_key": "strike_rate",
        "value_label": "SR",
    },
    "hundreds": {
        "title": "Centuries (100s)",
        "api_key": None,
        "value_label": "100s",
    },
    "fifties": {
        "title": "Half-Centuries (50s)",
        "api_key": None,
        "value_label": "50s",
    },
    "most_wickets": {
        "title": "Wickets",
        "api_key": "most_wickets",
        "value_label": "WKTS",
    },
    "bowling_average": {
        "title": "Bowling Average (Ave)",
        "api_key": "bowling_average",
        "value_label": "AVE",
    },
    "economy": {
        "title": "Economy Rate (Econ)",
        "api_key": "economy",
        "value_label": "ECON",
    },
    "bowling_strike_rate": {
        "title": "Strike Rate (SR)",
        "api_key": "bowling_strike_rate",
        "value_label": "SR",
    },
    "best_bowling": {
        "title": "Best Bowling Figures (BB)",
        "api_key": "best_bowling",
        "value_label": "BB",
    },
    "five_wickets": {
        "title": "Five-Wicket Hauls (5w)",
        "api_key": None,
        "value_label": "5w",
    },
}


def _stat_record_rows(value):
    """Find player record dictionaries inside a Cricbuzz record response."""
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            keys = set().union(*(item.keys() for item in value))
            if keys & {
                "player",
                "playerName",
                "name",
                "fullName",
                "playerDetails",
                "playerNameText",
            }:
                return value

        for item in value:
            found = _stat_record_rows(item)
            if found:
                return found

    elif isinstance(value, dict):
        for key in [
            "records",
            "record",
            "stats",
            "statsList",
            "values",
            "data",
            "content",
            "list",
            "items",
            "recordList",
        ]:
            if key in value:
                found = _stat_record_rows(value[key])
                if found:
                    return found

        for child in value.values():
            found = _stat_record_rows(child)
            if found:
                return found

    return []


def _nested_record_value(record, keys):
    """Read a scalar value from a Cricbuzz record dictionary."""
    for key in keys:
        value = record.get(key)

        if isinstance(value, dict):
            value = (
                value.get("name")
                or value.get("label")
                or value.get("displayName")
                or value.get("value")
                or value.get("text")
            )

        if value not in (None, ""):
            return value

    return None


def _stat_player_name(record):
    """Return the player name from common Cricbuzz record fields."""
    value = _nested_record_value(
        record,
        [
            "player",
            "playerName",
            "fullName",
            "name",
            "playerNameText",
            "batsman",
            "bowler",
        ],
    )

    if isinstance(value, dict):
        value = (
            value.get("name")
            or value.get("fullName")
            or value.get("playerName")
            or value.get("shortName")
        )

    return str(value).strip() if value not in (None, "") else ""


def _stat_team_name(record):
    """Return the team/country from common Cricbuzz record fields."""
    value = _nested_record_value(
        record,
        [
            "team",
            "teamName",
            "country",
            "teamFullName",
            "countryName",
        ],
    )

    if isinstance(value, dict):
        value = (
            value.get("teamName")
            or value.get("name")
            or value.get("shortName")
        )

    return str(value).strip() if value not in (None, "") else ""


def _is_missing_stat_value(value):
    """Reject empty and non-numeric placeholder values such as NaN."""
    if value in (None, ""):
        return True

    text = str(value).strip().lower()
    return text in {"nan", "none", "null", "n/a", "na", "-", "--"}


def _stat_value(record, stat_key):
    """Return the display value for one API record category."""
    key_map = {
        "most_runs": [
            "runs",
            "totalRuns",
            "run",
            "r",
            "value",
            "statValue",
        ],
        "highest_score": [
            "runs",
            "score",
            "highestScore",
            "highScore",
            "value",
            "statValue",
        ],
        "batting_average": [
            "avg",
            "average",
            "battingAverage",
            "batting_average",
            "value",
            "statValue",
        ],
        "strike_rate": [
            "sr",
            "strikeRate",
            "strike_rate",
            "battingStrikeRate",
            "value",
            "statValue",
        ],
        "most_wickets": [
            "wickets",
            "totalWickets",
            "w",
            "value",
            "statValue",
        ],
        "bowling_average": [
            "avg",
            "average",
            "bowlingAverage",
            "bowling_average",
            "value",
            "statValue",
        ],
        "economy": [
            "econ",
            "economy",
            "economyRate",
            "economy_rate",
            "value",
            "statValue",
        ],
        "bowling_strike_rate": [
            "sr",
            "strikeRate",
            "strike_rate",
            "bowlingStrikeRate",
            "bowling_strike_rate",
            "value",
            "statValue",
        ],
        "best_bowling": [
            "bestBowling",
            "bestBowlingInnings",
            "bestBowlingMatch",
            "bowling",
            "figures",
            "value",
            "statValue",
        ],
    }

    value = _nested_record_value(record, key_map.get(stat_key, []))

    if isinstance(value, (dict, list)):
        return None

    if _is_missing_stat_value(value):
        return None

    return value


def _format_stat_value(value, stat_key):
    """Format a record value for compact table display."""
    if _is_missing_stat_value(value):
        return ""

    text = str(value).strip()

    if stat_key in {
        "most_runs",
        "highest_score",
        "most_wickets",
        "hundreds",
        "fifties",
        "five_wickets",
    }:
        try:
            number = float(text)
            return (
                f"{int(number):,}"
                if number.is_integer()
                else f"{number:,.1f}"
            )
        except (TypeError, ValueError):
            return text

    if stat_key in {
        "batting_average",
        "strike_rate",
        "bowling_average",
        "economy",
        "bowling_strike_rate",
    }:
        try:
            return f"{float(text):,.2f}"
        except (TypeError, ValueError):
            return text

    return text


def _normalize_api_stat_rows(records_data, stat_key):
    """Normalize one Cricbuzz record response into player/value rows."""
    rows = _stat_record_rows(records_data)
    normalized = []

    for index, record in enumerate(rows, start=1):
        if not isinstance(record, dict):
            continue

        player = _stat_player_name(record)
        value = _stat_value(record, stat_key)

        if not player or value in (None, ""):
            continue

        rank = _nested_record_value(
            record,
            ["rank", "position", "ranking", "pos", "rankNo"],
        )
        team = _stat_team_name(record)

        normalized.append(
            {
                "Rank": _safe_int(rank, index),
                "Player": player,
                "Team": team or "",
                "Value": _format_stat_value(value, stat_key),
            }
        )

    if not normalized:
        return pd.DataFrame(columns=["Rank", "Player", "Team", "Value"])

    return (
        pd.DataFrame(normalized)
        .drop_duplicates(subset=["Player"], keep="first")
        .sort_values(["Rank", "Player"])
        .head(20)
        .reset_index(drop=True)
    )


def _player_key(name):
    """Create a stable case-insensitive player key for API/SQLite merging."""
    return " ".join(str(name or "").strip().lower().split())


def _sqlite_batting_stats(fmt):
    """Return the complete batting columns needed by the unified table."""
    db_format = "t20i" if fmt == "t20" else fmt

    query = """
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    COALESCE(pcs.runs_scored, 0) DESC,
                    COALESCE(p.real_name, p.player_name)
            ) AS Rank,
            COALESCE(
                NULLIF(TRIM(p.real_name), ''),
                NULLIF(TRIM(p.player_name), '')
            ) AS Player,
            COALESCE(NULLIF(TRIM(p.country), ''), 'Unknown') AS Team,
            COALESCE(pcs.runs_scored, 0) AS Runs,
            ROUND(pcs.batting_average, 2) AS Average,
            ROUND(pcs.strike_rate, 2) AS Strike_Rate,
            COALESCE(pcs.hundreds, 0) AS Hundreds,
            COALESCE(pcs.fifties, 0) AS Fifties
        FROM player_career_stats pcs
        JOIN players p
          ON p.player_id = pcs.player_id
        WHERE LOWER(TRIM(COALESCE(pcs.format, ''))) = ?
          AND COALESCE(p.admin_active, 1) = 1
          AND COALESCE(pcs.runs_scored, 0) > 0
        ORDER BY Runs DESC, Player
        LIMIT 20
    """

    try:
        return run_query(query, (db_format,))
    except Exception:
        return pd.DataFrame()


def _sqlite_bowling_stats(fmt):
    """Return the complete bowling columns needed by the unified table."""
    db_format = "t20i" if fmt == "t20" else fmt

    query = """
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY
                    COALESCE(pbs.wickets_taken, 0) DESC,
                    COALESCE(p.real_name, p.player_name)
            ) AS Rank,
            COALESCE(
                NULLIF(TRIM(p.real_name), ''),
                NULLIF(TRIM(p.player_name), '')
            ) AS Player,
            COALESCE(NULLIF(TRIM(p.country), ''), 'Unknown') AS Team,
            COALESCE(pbs.wickets_taken, 0) AS Wickets,
            ROUND(pbs.bowling_average, 2) AS Average,
            ROUND(pbs.economy_rate, 2) AS Economy,
            ROUND(pbs.bowling_strike_rate, 2) AS Strike_Rate,
            COALESCE(
                NULLIF(TRIM(pbs.best_bowling_innings), ''),
                'N/A'
            ) AS Best_Bowling,
            COALESCE(pbs.five_wickets, 0) AS Five_Wickets
        FROM player_bowling_stats pbs
        JOIN players p
          ON p.player_id = pbs.cricbuzz_player_id
        WHERE LOWER(TRIM(COALESCE(pbs.format, ''))) = ?
          AND COALESCE(p.admin_active, 1) = 1
          AND COALESCE(pbs.wickets_taken, 0) > 0
        ORDER BY Wickets DESC, Player
        LIMIT 20
    """

    try:
        return run_query(query, (db_format,))
    except Exception:
        return pd.DataFrame()


def _api_stat_lookup(top_player_data, stat_key):
    """Return normalized API/cache rows keyed by player."""
    if not isinstance(top_player_data, dict):
        return {}

    stats = top_player_data.get("stats")
    if not isinstance(stats, dict):
        return {}

    api_key = TOP_PLAYER_STAT_CONFIG.get(stat_key, {}).get("api_key")
    if not api_key:
        return {}

    rows = _normalize_api_stat_rows(
        stats.get(api_key, {}),
        api_key,
    )

    lookup = {}
    for _, row in rows.iterrows():
        key = _player_key(row.get("Player"))
        if key:
            lookup[key] = row.to_dict()

    return lookup


def _sqlite_batting_lookup(df):
    """Index SQLite batting rows by player."""
    if df is None or df.empty:
        return {}

    lookup = {}
    for _, row in df.iterrows():
        key = _player_key(row.get("Player"))
        if key:
            lookup[key] = row.to_dict()
    return lookup


def _sqlite_bowling_lookup(df):
    """Index SQLite bowling rows by player."""
    if df is None or df.empty:
        return {}

    lookup = {}
    for _, row in df.iterrows():
        key = _player_key(row.get("Player"))
        if key:
            lookup[key] = row.to_dict()
    return lookup


def _build_batting_table(fmt, top_player_data):
    """
    Build one unified batting leaderboard.

    API/cache records are preferred for the record categories. SQLite fills
    columns that the records endpoint does not expose, such as 100s and 50s.
    If the API/cache has no usable base records, SQLite becomes the base table.
    """
    sqlite_df = _sqlite_batting_stats(fmt)
    sqlite_lookup = _sqlite_batting_lookup(sqlite_df)
    api_base = _api_stat_lookup(top_player_data, "most_runs")

    if api_base:
        base_players = list(api_base.keys())[:20]
    else:
        base_players = list(sqlite_lookup.keys())[:20]

    if not base_players:
        return pd.DataFrame()

    api_lookups = {
        key: _api_stat_lookup(top_player_data, key)
        for key in [
            "most_runs",
            "batting_average",
            "strike_rate",
        ]
    }

    rows = []
    for rank, player_key in enumerate(base_players, start=1):
        sqlite_row = sqlite_lookup.get(player_key, {})
        api_base_row = api_base.get(player_key, {})

        player_name = (
            api_base_row.get("Player")
            or sqlite_row.get("Player")
            or "Unknown"
        )
        team = (
            api_base_row.get("Team")
            or sqlite_row.get("Team")
            or "Unknown"
        )

        def value_for(stat_key, sqlite_column):
            api_row = api_lookups.get(stat_key, {}).get(player_key, {})
            value = api_row.get("Value")
            if not _is_missing_stat_value(value):
                return value
            return sqlite_row.get(sqlite_column)

        rows.append(
            {
                "Rank": rank,
                "Player": player_name,
                "Team": team,
                "Runs (R)": value_for("most_runs", "Runs"),
                "Batting Average (Ave)": value_for(
                    "batting_average",
                    "Average",
                ),
                "Strike Rate (SR)": value_for(
                    "strike_rate",
                    "Strike_Rate",
                ),
                "100s": sqlite_row.get("Hundreds"),
                "50s": sqlite_row.get("Fifties"),
            }
        )

    return pd.DataFrame(rows)


def _build_bowling_table(fmt, top_player_data):
    """
    Build one unified bowling leaderboard.

    API/cache records are preferred for wickets, averages, economy, strike
    rate and best bowling. SQLite fills unavailable fields and provides the
    five-wicket haul count.
    """
    sqlite_df = _sqlite_bowling_stats(fmt)
    sqlite_lookup = _sqlite_bowling_lookup(sqlite_df)
    api_base = _api_stat_lookup(top_player_data, "most_wickets")

    if api_base:
        base_players = list(api_base.keys())[:20]
    else:
        base_players = list(sqlite_lookup.keys())[:20]

    if not base_players:
        return pd.DataFrame()

    api_lookups = {
        key: _api_stat_lookup(top_player_data, key)
        for key in [
            "most_wickets",
            "bowling_average",
            "economy",
            "bowling_strike_rate",
            "best_bowling",
        ]
    }

    rows = []
    for rank, player_key in enumerate(base_players, start=1):
        sqlite_row = sqlite_lookup.get(player_key, {})
        api_base_row = api_base.get(player_key, {})

        player_name = (
            api_base_row.get("Player")
            or sqlite_row.get("Player")
            or "Unknown"
        )
        team = (
            api_base_row.get("Team")
            or sqlite_row.get("Team")
            or "Unknown"
        )

        def value_for(stat_key, sqlite_column):
            api_row = api_lookups.get(stat_key, {}).get(player_key, {})
            value = api_row.get("Value")
            if not _is_missing_stat_value(value):
                return value
            return sqlite_row.get(sqlite_column)

        rows.append(
            {
                "Rank": rank,
                "Player": player_name,
                "Team": team,
                "Wickets": value_for("most_wickets", "Wickets"),
                "Bowling Average (Ave)": value_for(
                    "bowling_average",
                    "Average",
                ),
                "Economy Rate (Econ)": value_for(
                    "economy",
                    "Economy",
                ),
                "Strike Rate (SR)": value_for(
                    "bowling_strike_rate",
                    "Strike_Rate",
                ),
                "Best Bowling Figures (BB)": value_for(
                    "best_bowling",
                    "Best_Bowling",
                ),
                "5w": sqlite_row.get("Five_Wickets"),
            }
        )

    return pd.DataFrame(rows)


def _render_unified_player_table(df, columns, numeric_columns=None):
    """Render one compact leaderboard table using native Streamlit columns."""
    if df is None or df.empty:
        st.caption("No records available for this format.")
        return

    numeric_columns = numeric_columns or set()

    st.markdown(
        """
        <style>
        .top-stats-table-header {
            padding: 0 10px 6px 10px;
        }

        .top-stats-table-row {
            padding: 8px 10px 7px 10px;
            margin-bottom: 6px;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 9px;
            background: rgba(255,255,255,0.018);
        }

        .top-stats-table-row:hover {
            border-color: rgba(255,255,255,0.22);
            background: rgba(255,255,255,0.035);
        }

        .top-stats-table-row [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            line-height: 1.2 !important;
        }

        .top-stats-table-row [data-testid="stCaptionContainer"] {
            margin: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # First column is rank, second is player, third is team, remaining
    # columns contain the requested cricket statistics.
    weights = [0.62, 2.0, 1.35]
    weights.extend([1.0] * (len(columns) - 3))

    header_cols = st.columns(weights)
    for column, header in zip(header_cols, columns):
        column.caption(header.upper())

    for _, row in df.iterrows():
        row_cols = st.columns(weights)

        rank = _safe_int(row.get("Rank"), 0)
        if rank == 1:
            rank_display = "👑 #1"
        elif rank == 2:
            rank_display = "🥈 #2"
        elif rank == 3:
            rank_display = "🥉 #3"
        elif rank <= 5:
            rank_display = f"🔥 #{rank}"
        elif rank <= 10:
            rank_display = f"⚡ #{rank}"
        else:
            rank_display = f"🏅 #{rank}"

        for index, column in enumerate(columns):
            value = row.get(column, "")

            if pd.isna(value):
                value = ""

            if column == "Rank":
                display_value = rank_display
            elif column == "Player":
                display_value = f"**{str(value)}**"
            elif column == "Team":
                display_value = (
                    f"🌍 {str(value)}"
                    if str(value).strip()
                    else "—"
                )
            elif column in numeric_columns:
                try:
                    number = float(value)
                    if number.is_integer():
                        display_value = f"**{int(number):,}**"
                    else:
                        display_value = f"**{number:,.2f}**"
                except (TypeError, ValueError):
                    display_value = f"**{str(value)}**"
            else:
                display_value = f"**{str(value)}**"

            with row_cols[index]:
                st.markdown(display_value)

    st.caption(f"Top {len(df)} players • {fmt.upper()} • Combined API/cache + SQLite fallback")


# Top Players section

if section["key"] == "players":
    st.markdown("### ⭐ Top Player Stats")
    st.caption(
        "Top 15 batting and bowling leaders from the local ranking JSON cache."
    )

    fmt = st.selectbox(
        "Player stats format",
        ["odi", "test", "t20"],
        format_func=lambda x: x.upper(),
        key="player_ranking_format",
    )

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

    # Use the already-combined Top 15 ranking files.
    format_label = {
        "odi": "ODI",
        "test": "Test",
        "t20": "T20",
    }[fmt]

    cache_dir = PROJECT_ROOT / "data" / "api_cache"

    batting_path = cache_dir / f"Top_15_Batters_{format_label}.json"
    bowling_path = cache_dir / f"Top_15_Bowlers_{format_label}.json"

    def _load_combined_top_15(path, role):
        """Load one combined Top 15 ranking JSON file."""
        if not path.is_file():
            return pd.DataFrame()

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return pd.DataFrame()

        if not isinstance(payload, dict):
            return pd.DataFrame()

        players = payload.get("players")

        if not isinstance(players, list):
            return pd.DataFrame()

        rows = []

        for player in players:
            if not isinstance(player, dict):
                continue

            player_name = str(player.get("player", "")).strip()

            if not player_name:
                continue

            if role == "batting":
                rows.append(
                    {
                        "Rank": _safe_int(
                            player.get("rank"),
                            len(rows) + 1,
                        ),
                        "Player": player_name,
                        "Matches (M)": _safe_int(
                            player.get("matches")
                        ),
                        "Innings (I)": _safe_int(
                            player.get("innings")
                        ),
                        "Runs (R)": _safe_int(
                            player.get("runs")
                        ),
                        "Strike Rate (SR)": _safe_number(
                            player.get("strike_rate")
                        ),
                    }
                )
            else:
                rows.append(
                    {
                        "Rank": _safe_int(
                            player.get("rank"),
                            len(rows) + 1,
                        ),
                        "Player": player_name,
                        "Matches (M)": _safe_int(
                            player.get("matches")
                        ),
                        "Overs (O)": player.get("overs", ""),
                        "Wickets (W)": _safe_int(
                            player.get("wickets")
                        ),
                        "Economy (Eco)": _safe_number(
                            player.get("economy")
                        ),
                    }
                )

        if not rows:
            return pd.DataFrame()

        return (
            pd.DataFrame(rows)
            .sort_values(
                ["Rank", "Player"],
                kind="stable",
            )
            .drop_duplicates(
                subset=["Rank", "Player"],
                keep="first",
            )
            .head(15)
            .reset_index(drop=True)
        )

    batting_df = _load_combined_top_15(
        batting_path,
        "batting",
    )
    bowling_df = _load_combined_top_15(
        bowling_path,
        "bowling",
    )

    # Style the player leaderboards to match the team leaderboard visual
    # while preserving the original table column headers.
    st.markdown(
        """
        <style>
        .player-board-title {
            margin-bottom: 0.10rem;
        }

        .player-board-subtitle {
            color: rgba(255,255,255,0.55);
            font-size: 0.76rem;
            margin-bottom: 0.55rem;
        }

        .player-board-header {
            color: rgba(255,255,255,0.55);
            font-size: 0.67rem;
            font-weight: 800;
            letter-spacing: 0.035em;
            white-space: nowrap;
        }

        .player-board-rank {
            font-size: 0.88rem;
            font-weight: 800;
        }

        .player-board-player {
            font-size: 0.88rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .player-board-meta {
            color: rgba(255,255,255,0.48);
            font-size: 0.67rem;
            margin-top: 0.16rem;
        }

        .player-board-value {
            font-size: 0.86rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .player-board-row {
            min-height: 64px;
        }

        .player-board-row [data-testid="stVerticalBlockBorderWrapper"] {
            background:
                linear-gradient(
                    90deg,
                    rgba(255,255,255,0.018),
                    rgba(255,255,255,0.008)
                ) !important;
            border-color: rgba(255,255,255,0.12) !important;
            transition:
                border-color 0.18s ease,
                background 0.18s ease,
                transform 0.18s ease;
        }

        .player-board-row [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(145,150,255,0.34) !important;
            background:
                linear-gradient(
                    90deg,
                    rgba(120,126,255,0.075),
                    rgba(255,255,255,0.015)
                ) !important;
            transform: translateY(-1px);
        }

        .player-board-row [data-testid="stProgress"] {
            margin-top: 0.18rem !important;
            margin-bottom: 0 !important;
        }

        .player-board-row [data-testid="stProgress"] > div {
            height: 0.25rem !important;
        }

        .player-board-empty {
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    def _rank_display(rank):
        if rank == 1:
            return "👑 #1"
        if rank == 2:
            return "🥈 #2"
        if rank == 3:
            return "🥉 #3"
        if rank <= 5:
            return f"🔥 #{rank}"
        if rank <= 10:
            return f"⚡ #{rank}"
        return f"🏅 #{rank}"

    def _rank_badge(rank):
        if rank == 1:
            return "LEGEND"
        if rank in {2, 3}:
            return "ELITE"
        if rank <= 5:
            return "TOP 5"
        if rank <= 10:
            return "TOP 10"
        return "TOP 15"

    def _render_player_leaderboard(df, role):
        """Render one attractive leaderboard using the original headers."""
        if role == "batting":
            title = "🏏 Cricket Batting Stats"
            subtitle = "Top 15 players ranked by Runs (R)."
            columns = [
                "Rank",
                "Player",
                "Matches (M)",
                "Innings (I)",
                "Runs (R)",
                "Strike Rate (SR)",
            ]
            primary_column = "Runs (R)"
            secondary_column = "Strike Rate (SR)"
            detail_column = "Innings (I)"
        else:
            title = "🎯 Key Bowling Statistics"
            subtitle = "Top 15 players ranked by Wickets (W)."
            columns = [
                "Rank",
                "Player",
                "Matches (M)",
                "Overs (O)",
                "Wickets (W)",
                "Economy (Eco)",
            ]
            primary_column = "Wickets (W)"
            secondary_column = "Economy (Eco)"
            detail_column = "Overs (O)"

        st.markdown(
            f'<div class="player-board-title"><h3>{title}</h3></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="player-board-subtitle">'
            f'{subtitle} • {format_label}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Keep the exact original column headers.
        header_cols = st.columns(
            [0.70, 1.90, 1.05, 1.05, 1.00, 1.15]
        )

        for column, header in zip(header_cols, columns):
            column.markdown(
                f'<div class="player-board-header">{header.upper()}</div>',
                unsafe_allow_html=True,
            )

        if df.empty:
            with st.container(
                border=True,
                key=f"empty_player_board_{role}_{fmt}",
            ):
                st.markdown(
                    '<div class="player-board-empty">'
                    'No ranking data is available.'
                    '</div>',
                    unsafe_allow_html=True,
                )
            return

        visible_df = df.head(15).copy()

        max_primary = max(
            float(
                pd.to_numeric(
                    visible_df[primary_column],
                    errors="coerce",
                ).fillna(0).max()
            ),
            1.0,
        )

        for _, player in visible_df.iterrows():
            rank = _safe_int(player.get("Rank"), 0)
            player_name = str(
                player.get("Player", "Unknown")
            ).strip()

            matches = _safe_int(
                player.get("Matches (M)"),
                0,
            )

            primary_value = _safe_number(
                player.get(primary_column),
                0,
            )

            secondary_value = _safe_number(
                player.get(secondary_column),
                0,
            )

            power = min(
                max(primary_value / max_primary, 0.0),
                1.0,
            )

            rank_display = _rank_display(rank)
            badge = _rank_badge(rank)

            with st.container(
                border=True,
                key=f"{role}_leaderboard_row_{fmt}_{rank}_{player_name}",
            ):
                st.markdown(
                    '<div class="player-board-row"></div>',
                    unsafe_allow_html=True,
                )

                row_cols = st.columns(
                    [0.70, 1.90, 1.05, 1.05, 1.00, 1.15]
                )

                with row_cols[0]:
                    st.markdown(
                        f'<div class="player-board-rank">'
                        f'{rank_display}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(badge)

                with row_cols[1]:
                    st.markdown(
                        f'<div class="player-board-player">'
                        f'{player_name}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="player-board-meta">'
                        f'{matches:,} matches'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                with row_cols[2]:
                    st.markdown(
                        f'<div class="player-board-value">'
                        f'{matches:,}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                with row_cols[3]:
                    detail_value = player.get(
                        detail_column,
                        "",
                    )

                    if role == "batting":
                        detail_display = _safe_int(
                            detail_value,
                            0,
                        )
                        detail_text = f"{detail_display:,}"
                    else:
                        detail_text = str(
                            detail_value
                        ).strip()

                    st.markdown(
                        f'<div class="player-board-value">'
                        f'{detail_text}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                with row_cols[4]:
                    if primary_value.is_integer():
                        primary_display = (
                            f"{int(primary_value):,}"
                        )
                    else:
                        primary_display = (
                            f"{primary_value:,.2f}"
                        )

                    st.markdown(
                        f'<div class="player-board-value">'
                        f'{primary_display}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(
                        power,
                        text=None,
                    )

                with row_cols[5]:
                    st.markdown(
                        f'<div class="player-board-value">'
                        f'{secondary_value:,.2f}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # Keep the two complete leaderboards side by side.
    board_cols = st.columns(2)

    with board_cols[0]:
        _render_player_leaderboard(
            batting_df,
            "batting",
        )

    with board_cols[1]:
        _render_player_leaderboard(
            bowling_df,
            "bowling",
        )


# Fantasy Cricket section

def _fantasy_impact_score(runs, strike_rate, fifty_count, innings):
    """Create a simple analytics-based fantasy impact score out of 100."""
    if innings <= 0:
        return 0

    run_component = min(float(runs) / 50.0, 1.0) * 45
    sr_component = min(float(strike_rate) / 140.0, 1.0) * 25
    fifty_component = min(float(fifty_count) / max(innings * 0.35, 1.0), 1.0) * 20
    consistency_component = min(float(innings) / 10.0, 1.0) * 10

    return int(round(
        run_component
        + sr_component
        + fifty_component
        + consistency_component
    ))


def _fantasy_form_badge(runs):
    """Return a simple fantasy form label from recent runs."""
    if runs >= 75:
        return "🔥 ON FIRE"
    if runs >= 50:
        return "🚀 IMPACT"
    if runs >= 30:
        return "📈 SOLID"
    if runs >= 15:
        return "⚡ STEADY"
    return "🧊 COLD"


def _fantasy_points_for_innings(runs, balls, strike_rate):
    """Estimate fantasy impact points for analytics only."""
    runs = max(float(runs), 0.0)
    balls = max(float(balls), 0.0)
    strike_rate = max(float(strike_rate), 0.0)

    points = runs

    if runs >= 50:
        points += 10
    if runs >= 100:
        points += 10
    if strike_rate >= 150 and balls >= 10:
        points += 8
    elif strike_rate >= 120 and balls >= 10:
        points += 4

    return int(round(points))


def _render_fantasy_form_board(form_df, selected_player):
    """Render recent batting form as a fantasy-style performance board."""
    if form_df.empty:
        return

    data = form_df.copy()
    data["Runs"] = pd.to_numeric(data["Runs"], errors="coerce").fillna(0)
    data["Balls"] = pd.to_numeric(data["Balls"], errors="coerce").fillna(0)
    data["Strike_Rate"] = pd.to_numeric(
        data["Strike_Rate"], errors="coerce"
    ).fillna(0)

    innings = len(data)
    avg_runs = float(data["Runs"].mean())
    avg_sr = float(data["Strike_Rate"].mean())
    fifties = int((data["Runs"] >= 50).sum())
    hundreds = int((data["Runs"] >= 100).sum())
    impact = _fantasy_impact_score(avg_runs, avg_sr, fifties, innings)

    recent_runs = data["Runs"].tolist()
    recent_average = sum(recent_runs[:3]) / max(min(3, len(recent_runs)), 1)
    previous_average = (
        sum(recent_runs[3:6]) / len(recent_runs[3:6])
        if len(recent_runs) > 3
        else recent_average
    )
    trend_delta = recent_average - previous_average

    if impact >= 80:
        tier = "🏆 ELITE PICK"
    elif impact >= 65:
        tier = "💎 PREMIUM PICK"
    elif impact >= 50:
        tier = "⭐ VALUE PICK"
    else:
        tier = "🔎 DIFFERENTIAL"

    st.markdown(f"#### 🎮 {selected_player} — Fantasy Performance Card")

    with st.container(border=True):
        top = st.columns([2.1, 1, 1, 1, 1])

        with top[0]:
            st.markdown(f"### {tier}")
            st.caption("Analytics-based fantasy signal • Not an official platform score")

        with top[1]:
            st.metric("Impact Score", f"{impact}/100")

        with top[2]:
            st.metric("Avg Runs", f"{avg_runs:.1f}")

        with top[3]:
            st.metric("Avg SR", f"{avg_sr:.1f}")

        with top[4]:
            st.metric("50+", fifties)

        st.progress(
            min(max(impact / 100, 0.0), 1.0),
            text=f"Fantasy Impact Power • {impact}%",
        )

        if trend_delta > 5:
            trend_text = f"📈 Form rising • +{trend_delta:.1f} runs vs previous 3 innings"
        elif trend_delta < -5:
            trend_text = f"📉 Form cooling • {trend_delta:.1f} runs vs previous 3 innings"
        else:
            trend_text = "➖ Form stable across the recent sample"

        st.caption(trend_text)

    st.markdown("##### 🧩 Recent Innings Battle Board")

    board = data.head(10).copy()
    board["Fantasy Points"] = board.apply(
        lambda row: _fantasy_points_for_innings(
            row["Runs"], row["Balls"], row["Strike_Rate"]
        ),
        axis=1,
    )

    max_runs = max(float(board["Runs"].max()), 1.0)

    for position, (_, row) in enumerate(board.iterrows(), start=1):
        runs = float(row["Runs"])
        balls = float(row["Balls"])
        sr = float(row["Strike_Rate"])
        points = int(row["Fantasy Points"])
        badge = _fantasy_form_badge(runs)
        match_date = str(row.get("Match_Date", ""))[:10]
        match_format = str(row.get("Format", "Unknown")).upper()
        opposition = str(row.get("Opposition", "Unknown"))
        ground = str(row.get("Ground", "Unknown"))

        with st.container(border=True):
            row_cols = st.columns([0.45, 1.25, 0.75, 1.25, 1.0, 1.0, 1.8, 1.0])

            with row_cols[0]:
                st.markdown(f"**#{position}**")

            with row_cols[1]:
                st.markdown(f"**{badge}**")
                st.caption(match_date)

            with row_cols[2]:
                st.markdown(f"**{match_format}**")
                st.caption("Format")

            with row_cols[3]:
                st.markdown(f"**{runs:.0f} runs**")
                st.caption(f"{balls:.0f} balls")

            with row_cols[4]:
                st.markdown(f"**{sr:.1f}**")
                st.caption("Strike Rate")

            with row_cols[4]:
                st.markdown(f"**+{points}**")
                st.caption("Impact pts")

            with row_cols[5]:
                st.caption(f"vs {opposition} • {ground}")
                st.progress(
                    min(max(runs / max_runs, 0.0), 1.0),
                    text=f"Run Power • {runs / max_runs * 100:.0f}%",
                )

            with row_cols[6]:
                if runs >= 100:
                    result = "💯 CENTURY"
                elif runs >= 50:
                    result = "🏅 FIFTY"
                elif runs == 0:
                    result = "🧊 DUCK"
                else:
                    result = "🏏 CONTRIBUTION"
                st.markdown(f"**{result}**")

    if hundreds:
        st.success(
            f"💯 {selected_player} has {hundreds} century-level score(s) in this sample."
        )


def _render_h2h_battle(team1, team2, h2h_df):
    """Render head-to-head as a fantasy matchup battle."""
    winners = h2h_df["winner"].fillna("").astype(str).str.lower()

    team1_wins = int((winners == team1.lower()).sum())
    team2_wins = int((winners == team2.lower()).sum())
    other = max(len(h2h_df) - team1_wins - team2_wins, 0)
    decided = team1_wins + team2_wins

    if decided:
        team1_pct = team1_wins / decided
        team2_pct = team2_wins / decided
    else:
        team1_pct = 0.5
        team2_pct = 0.5

    if team1_wins > team2_wins:
        edge_text = f"🟢 {team1} has the historical edge"
        edge_team = team1
    elif team2_wins > team1_wins:
        edge_text = f"🟢 {team2} has the historical edge"
        edge_team = team2
    else:
        edge_text = "🟡 Historical matchup is level"
        edge_team = "Even"

    with st.container(border=True):
        battle_cols = st.columns([1, 0.6, 1])

        with battle_cols[0]:
            st.markdown(f"### 🛡️ {team1}")
            st.metric("Wins", team1_wins)

        with battle_cols[1]:
            st.markdown("### ⚔️")
            st.metric("Matches", len(h2h_df))

        with battle_cols[2]:
            st.markdown(f"### 🛡️ {team2}")
            st.metric("Wins", team2_wins)

        st.progress(
            team1_pct,
            text=f"{team1} {team1_pct * 100:.0f}%  vs  {team2} {team2_pct * 100:.0f}% of decided matches",
        )
        st.caption(edge_text)

        if edge_team != "Even":
            st.info(
                f"🎯 Fantasy selection signal: {edge_team} has the stronger historical matchup record."
            )
        else:
            st.info(
                "🎯 Fantasy selection signal: use recent player form and current match conditions as the tie-breaker."
            )


def _render_live_fantasy_board(live_df):
    """Render live matches as fantasy monitoring cards instead of a plain table."""
    if live_df.empty:
        st.info("No live matches are currently available.")
        return

    st.markdown("##### 🔴 Live Fantasy Match Center")
    st.caption(
        "Follow match state and identify where fantasy points are likely to change quickly."
    )

    for index, (_, match) in enumerate(live_df.iterrows(), start=1):
        teams = str(match.get("Teams", "Match"))
        status = str(match.get("Status", "Live"))
        score = str(match.get("Score", ""))

        with st.container(border=True):
            cols = st.columns([2.4, 1.5, 2.6, 0.8])

            with cols[0]:
                st.markdown(f"### 🏏 {teams}")
                st.caption(f"Fantasy Match #{index}")

            with cols[1]:
                status_lower = status.lower()
                if "won" in status_lower:
                    badge = "🏆 FINISHED"
                elif "need" in status_lower:
                    badge = "🔥 CHASE ON"
                else:
                    badge = "🔴 LIVE"
                st.markdown(f"**{badge}**")

            with cols[2]:
                st.markdown(f"**{score or status}**")
                if score and score != status:
                    st.caption(status)

            with cols[3]:
                st.markdown("**⚡**")
                st.caption("LIVE")


if section["key"] == "fantasy":
        st.markdown("### 🎮 Fantasy Cricket Arena")

        fantasy_tabs = st.tabs(
            [
                "📈 Player Form",
                "🤝 Head-to-Head",
                "🔴 Live Scores",
            ]
        )

        # Player form
        with fantasy_tabs[0]:
            player_names = _current_player_names()

            if not player_names:
                st.info("No player form records are available.")
            else:
                selected_player = st.selectbox(
                    "Select your fantasy player",
                    player_names,
                    key="fantasy_player",
                )

                form_df = _find_player_form(selected_player)

                if form_df.empty:
                    st.info(
                        f"No recent batting innings found for {selected_player}."
                    )
                else:
                    runs = pd.to_numeric(
                        form_df["Runs"],
                        errors="coerce",
                    ).fillna(0)
                    sr = pd.to_numeric(
                        form_df["Strike_Rate"],
                        errors="coerce",
                    ).fillna(0)

                    recent_avg = float(runs.head(3).mean())
                    average_runs = float(runs.mean())
                    average_sr = float(sr.mean())
                    fifty_count = int((runs >= 50).sum())

                    # Selected player content
                    _render_fantasy_form_board(
                        form_df,
                        selected_player,
                    )

                    # Dynamic fantasy scout panel in the Streamlit sidebar
                    with st.sidebar:
                        st.markdown(
                            """
                            <style>
                            .scout-card-title {
                                font-weight: 800;
                                font-size: 0.82rem;
                                line-height: 1.15;
                            }

                            .scout-card-stat {
                                font-size: 1.28rem;
                                font-weight: 850;
                                line-height: 1.05;
                                margin-top: 0.28rem;
                            }

                            .scout-card-label {
                                color: rgba(255,255,255,0.62);
                                font-size: 0.69rem;
                                margin-top: 0.10rem;
                            }

                            .scout-card-target {
                                color: rgba(255,255,255,0.50);
                                font-size: 0.68rem;
                                line-height: 1.2;
                                margin-top: 0.28rem;
                            }

                            .scout-card-good {
                                color: #79d99a;
                            }

                            .scout-card-watch {
                                color: #ffd166;
                            }
                            </style>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown("### 🧠 Scout Checklist")
                        st.caption(
                            f"Live assessment for **{selected_player}**"
                        )

                        # Run production
                        with st.container(border=True):
                            run_good = average_runs >= 40
                            status_icon = "✅" if run_good else "⚠️"
                            status_class = (
                                "scout-card-good"
                                if run_good
                                else "scout-card-watch"
                            )
                            status_text = (
                                "Strong run production"
                                if run_good
                                else "Run production to watch"
                            )
                            run_progress = min(
                                max(average_runs / 40, 0.0),
                                1.0,
                            )

                            st.markdown(
                                f'<div class="scout-card-title {status_class}">'
                                f'{status_icon} {status_text}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="scout-card-stat">'
                                f'{average_runs:.1f}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                '<div class="scout-card-label">'
                                'Average runs per innings'
                                '</div>',
                                unsafe_allow_html=True,
                            )
                            st.progress(run_progress, text=None)
                            st.markdown(
                                '<div class="scout-card-target">'
                                'Target: 40+ runs'
                                '</div>',
                                unsafe_allow_html=True,
                            )

                        # Strike-rate boost
                        with st.container(border=True):
                            sr_good = average_sr >= 100
                            status_icon = "✅" if sr_good else "⚠️"
                            status_class = (
                                "scout-card-good"
                                if sr_good
                                else "scout-card-watch"
                            )
                            status_text = (
                                "Strike-rate boost"
                                if sr_good
                                else "Strike rate to watch"
                            )
                            sr_progress = min(
                                max(average_sr / 100, 0.0),
                                1.0,
                            )

                            st.markdown(
                                f'<div class="scout-card-title {status_class}">'
                                f'{status_icon} {status_text}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="scout-card-stat">'
                                f'{average_sr:.1f}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                '<div class="scout-card-label">'
                                'Average strike rate'
                                '</div>',
                                unsafe_allow_html=True,
                            )
                            st.progress(sr_progress, text=None)
                            st.markdown(
                                '<div class="scout-card-target">'
                                'Target: 100+ SR'
                                '</div>',
                                unsafe_allow_html=True,
                            )

                        # Boundary potential
                        with st.container(border=True):
                            boundary_good = fifty_count >= 2
                            status_icon = "🔥" if boundary_good else "🔎"
                            status_class = (
                                "scout-card-good"
                                if boundary_good
                                else "scout-card-watch"
                            )
                            status_text = (
                                "Boundary potential"
                                if boundary_good
                                else "Boundary upside"
                            )
                            boundary_progress = min(
                                max(fifty_count / 2, 0.0),
                                1.0,
                            )

                            st.markdown(
                                f'<div class="scout-card-title {status_class}">'
                                f'{status_icon} {status_text}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="scout-card-stat">'
                                f'{fifty_count}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                '<div class="scout-card-label">'
                                'Scores of 50+ in available form'
                                '</div>',
                                unsafe_allow_html=True,
                            )
                            st.progress(
                                boundary_progress,
                                text=None,
                            )
                            st.markdown(
                                '<div class="scout-card-target">'
                                'Target: 2+ scores of 50'
                                '</div>',
                                unsafe_allow_html=True,
                            )

                        # Recent momentum
                        with st.container(border=True):
                            momentum_good = recent_avg >= average_runs
                            status_icon = "📈" if momentum_good else "➖"
                            status_class = (
                                "scout-card-good"
                                if momentum_good
                                else "scout-card-watch"
                            )
                            status_text = (
                                "Recent momentum"
                                if momentum_good
                                else "Stable momentum"
                            )

                            momentum_ratio = (
                                recent_avg / average_runs
                                if average_runs > 0
                                else 0.0
                            )
                            momentum_progress = min(
                                max(momentum_ratio, 0.0),
                                1.0,
                            )

                            delta_runs = recent_avg - average_runs
                            delta_text = (
                                f"+{delta_runs:.1f}"
                                if delta_runs >= 0
                                else f"{delta_runs:.1f}"
                            )

                            st.markdown(
                                f'<div class="scout-card-title {status_class}">'
                                f'{status_icon} {status_text}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="scout-card-stat">'
                                f'{recent_avg:.1f}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                '<div class="scout-card-label">'
                                'Average runs across last 3 innings'
                                '</div>',
                                unsafe_allow_html=True,
                            )
                            st.progress(
                                momentum_progress,
                                text=None,
                            )
                            st.markdown(
                                f'<div class="scout-card-target">'
                                f'vs overall average: {delta_text} runs'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                        st.caption(
                            "💡 The indicators update automatically when you "
                            "switch the selected player."
                        )


        # Head-to-head
        with fantasy_tabs[1]:
            st.markdown("#### 🤝 Fantasy Matchup Battle")
            st.caption(
                "Three-year historical H2H results using ICC ODI-ranked teams only."
            )

            # Use ICC ODI-ranked teams only for fantasy H2H selection.
            try:
                odi_rankings_data = get_icc_team_rankings("odi")
                odi_rankings_df = _normalize_team_rankings(odi_rankings_data)
            except Exception:
                odi_rankings_df = pd.DataFrame()

            # Fall back to the imported ICC ODI ranking table if the API/cache
            # does not currently return ranking data.
            if odi_rankings_df.empty:
                try:
                    odi_rankings_df = run_query(
                        """
                        SELECT
                            position AS Rank,
                            team AS Team,
                            rating AS Rating,
                            matches AS Matches,
                            points AS Points,
                            imported_at AS "Last Updated"
                        FROM icc_rankings_teams
                        WHERE LOWER(format) = 'odi'
                        ORDER BY position
                        """
                    )
                except Exception:
                    odi_rankings_df = pd.DataFrame()

            team_options = (
                odi_rankings_df["Team"]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda series: series.ne("")]
                .drop_duplicates()
                .tolist()
                if not odi_rankings_df.empty and "Team" in odi_rankings_df.columns
                else []
            )

            if len(team_options) < 2:
                st.info("Not enough team data is available.")
            else:
                h2h_cols = st.columns(2)

                with h2h_cols[0]:
                    h2h_team1 = st.selectbox(
                        "🛡️ Choose Team A",
                        team_options,
                        key="fantasy_h2h_team1",
                    )

                with h2h_cols[1]:
                    available_team2 = [
                        team for team in team_options if team != h2h_team1
                    ]
                    h2h_team2 = st.selectbox(
                        "🛡️ Choose Team B",
                        available_team2,
                        key="fantasy_h2h_team2",
                    )

                h2h_df = _find_match_rows(
                    h2h_team1,
                    h2h_team2,
                    years=3,
                )

                if h2h_df.empty:
                    st.info("No H2H matches found in the last three years.")
                else:
                    _render_h2h_battle(h2h_team1, h2h_team2, h2h_df)

                    st.markdown("##### 📜 Matchup History")
                    display_columns = [
                        column
                        for column in [
                            "match_date",
                            "team1",
                            "team2",
                            "winner",
                            "match_type",
                        ]
                        if column in h2h_df.columns
                    ]

                    history_df = h2h_df[display_columns].copy()
                    history_df.columns = [
                        "Date",
                        "Team A",
                        "Team B",
                        "Winner",
                        "Format",
                    ]
                    st.dataframe(
                        history_df,
                        use_container_width=True,
                        hide_index=True,
                    )

        # Live scores
        with fantasy_tabs[2]:
            st.markdown("#### 🔴 Fantasy Match Center")
            st.caption(
                "Live Cricbuzz scores are loaded through the existing cache-first live-score layer."
            )

            if st.button(
                "🔄 Refresh Live Scores",
                key="fantasy_live_refresh",
            ):
                st.rerun()

            try:
                live_data = get_live_matches(force_refresh=True)
                live_df = _normalize_live_matches(live_data)
            except Exception as exc:
                live_df = pd.DataFrame()
                st.warning(f"Live score data is unavailable: {exc}")

            if not live_df.empty:
                _render_live_fantasy_board(live_df)
                st.success(
                    f"🔴 {len(live_df)} live match(es) available for fantasy monitoring."
                )
