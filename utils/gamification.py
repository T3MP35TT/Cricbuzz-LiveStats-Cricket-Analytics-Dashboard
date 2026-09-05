"""
Shared gamification engine for Cricbuzz LiveStats.

Import this from every page (Home, Live Matches, Top Player Stats,
SQL Queries, CRUD Operations) so XP, levels, streaks, badges, and
missions stay consistent across the whole app — Streamlit shares
st.session_state across all pages in a multi-page app.
"""

import datetime

import streamlit as st


AVATARS = ["🏏", "🦁", "🐉", "🦅", "🐯", "🦈", "🔥", "⚡"]

BADGES = [
    {"name": "Rookie Analyst", "xp": 0, "icon": "🎒"},
    {"name": "Data Digger", "xp": 100, "icon": "⛏️"},
    {"name": "Stat Sultan", "xp": 300, "icon": "👑"},
    {"name": "Cricket Guru", "xp": 600, "icon": "🧙"},
    {"name": "LiveStats Legend", "xp": 1000, "icon": "🏆"},
]

MISSIONS = [
    {
        "key": "live",
        "icon": "🔴",
        "title": "Catch a Live Match",
        "desc": "Visit Live Matches and check today's scores.",
        "xp": 20,
    },
    {
        "key": "players",
        "icon": "🏆",
        "title": "Scout the Leaderboards",
        "desc": "Visit Top Player Stats and find your favorite player.",
        "xp": 20,
    },
    {
        "key": "sql",
        "icon": "🧠",
        "title": "Crack a Query",
        "desc": "Open SQL Queries & Analytics and run any 1 of the 25 questions.",
        "xp": 30,
    },
    {
        "key": "crud",
        "icon": "🛠️",
        "title": "Manage the Roster",
        "desc": "Add or edit a player record in CRUD Operations.",
        "xp": 30,
    },
]


# ────────────────────────────────────────────────────────────────────────────
# State
# ────────────────────────────────────────────────────────────────────────────
def init_game_state():
    """Call this near the top of every page, before rendering anything."""
    defaults = {
        "player_name": "Guest Fan",
        "avatar": "🏏",
        "xp": 0,
        "coins": 0,
        "streak": 1,
        "last_visit": str(datetime.date.today()),
        "missions_done": set(),
        "quiz_date": "",
        "quiz_answered": False,
        "predictions": {},        # match_id -> {"team": str, "resolved": bool}
        "scorecards_viewed": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Streak tracking: bump on a new day, reset if a day was skipped.
    today = datetime.date.today()
    last = datetime.date.fromisoformat(st.session_state["last_visit"])
    if today != last:
        gap = (today - last).days
        st.session_state["streak"] = st.session_state["streak"] + 1 if gap == 1 else 1
        st.session_state["last_visit"] = str(today)
        st.session_state["quiz_answered"] = False


def add_xp(amount, coins=0):
    """Adds XP/coins and returns True if the player leveled up."""
    old_level = level_for(st.session_state["xp"])
    st.session_state["xp"] += amount
    st.session_state["coins"] += coins
    new_level = level_for(st.session_state["xp"])
    return new_level > old_level


def level_for(xp):
    return xp // 100 + 1


def xp_progress(xp):
    return (xp % 100) / 100


def current_badge(xp):
    unlocked = [b for b in BADGES if xp >= b["xp"]]
    return unlocked[-1] if unlocked else BADGES[0]


def next_badge(xp):
    for b in BADGES:
        if xp < b["xp"]:
            return b
    return None


def complete_mission(key, celebrate=True):
    """
    Marks a mission complete and grants its XP, but only the first time.
    Returns True if this call actually granted the reward (so callers can
    avoid double-toasting on reruns if they want finer control).
    """
    if key in st.session_state["missions_done"]:
        return False

    mission = next((m for m in MISSIONS if m["key"] == key), None)
    if mission is None:
        return False

    st.session_state["missions_done"].add(key)
    leveled_up = add_xp(mission["xp"])

    if celebrate:
        st.toast(f"🎯 Mission complete: {mission['title']} (+{mission['xp']} XP)", icon="🎉")
        if leveled_up:
            st.balloons()

    return True


# ────────────────────────────────────────────────────────────────────────────
# Reusable UI
# ────────────────────────────────────────────────────────────────────────────
def render_profile_strip():
    """A compact horizontal profile bar to drop near the top of any page."""
    xp = st.session_state["xp"]
    lvl = level_for(xp)
    badge = current_badge(xp)

    c1, c2, c3, c4, c5 = st.columns([1.3, 1.3, 1.3, 1.3, 3])
    c1.metric(f"{st.session_state['avatar']} Level", lvl)
    c2.metric("⭐ XP", xp)
    c3.metric("🔥 Streak", f"{st.session_state['streak']}d")
    c4.metric("🪙 Coins", st.session_state["coins"])
    with c5:
        st.write("")
        st.progress(
            xp_progress(xp),
            text=f"{badge['icon']} {badge['name']} · {xp % 100}/100 XP to next level",
        )