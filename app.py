import base64
import sys
from pathlib import Path

import streamlit as st


# Project root

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


try:
    from utils.db_connection import init_schema
except ImportError:
    # Lets this file run standalone even if the real db module isn't wired up yet.
    init_schema = None


st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
)



# Sidebar navigation styling
st.markdown(
    """
    <style>
    /* Sidebar navigation container */
    [data-testid="stSidebarNav"] {
        padding: 14px 10px 10px 10px;
    }

    [data-testid="stSidebarNav"] ul {
        padding: 0 !important;
        margin: 0 !important;
    }

    [data-testid="stSidebarNav"] li {
        margin: 5px 0 !important;
        padding: 0 !important;
    }

    /* Navigation links */
    [data-testid="stSidebarNav"] a {
        display: flex !important;
        align-items: center !important;
        min-height: 44px !important;
        padding: 0 14px !important;
        border-radius: 12px !important;
        border: 1px solid transparent !important;
        color: rgba(255,255,255,0.78) !important;
        background: transparent !important;
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

    /* Navigation text */
    [data-testid="stSidebarNav"] a span {
        color: inherit !important;
    }

    /* Hover */
    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;
        background: rgba(255,255,255,0.075) !important;
        border-color: rgba(255,255,255,0.12) !important;
        transform: translateX(3px) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18) !important;
    }

    /* Active page */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        color: #ffffff !important;
        background:
            linear-gradient(
                90deg,
                rgba(125, 130, 255, 0.24),
                rgba(255,255,255,0.07)
            ) !important;
        border-color: rgba(150,155,255,0.30) !important;
        box-shadow:
            inset 3px 0 0 rgba(175,180,255,0.95),
            0 7px 20px rgba(0,0,0,0.22) !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]:hover {
        transform: translateX(2px) !important;
    }

    /* Small active indicator */
    [data-testid="stSidebarNav"] a[aria-current="page"]::before {
        content: "";
        width: 5px;
        height: 5px;
        margin-right: 10px;
        border-radius: 50%;
        background: rgba(205,210,255,0.95);
        box-shadow: 0 0 9px rgba(170,175,255,0.75);
        flex: 0 0 auto;
    }

    /* Keep inactive links aligned with active links */
    [data-testid="stSidebarNav"] a:not([aria-current="page"])::before {
        content: "";
        width: 5px;
        height: 5px;
        margin-right: 10px;
        border-radius: 50%;
        background: rgba(255,255,255,0.18);
        flex: 0 0 auto;
    }

    /* Sidebar navigation separator */
    [data-testid="stSidebarNav"]::after {
        content: "CRICBUZZ LIVESTATS";
        display: block;
        margin: 16px 10px 4px 14px;
        padding-top: 12px;
        border-top: 1px solid rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.30);
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 1.5px;
    }

    /* Improve sidebar spacing around the navigation */
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────────────────
# Configuration
# Theme images used by the home page.

IMAGE_DIR = PROJECT_ROOT / "data" / "Images"
HEADER_IMAGE = IMAGE_DIR / "header.jpg"
BACKGROUND_IMAGE = IMAGE_DIR / "background.jpg"


def encode_image(path):
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode()


header = encode_image(HEADER_IMAGE)
background = encode_image(BACKGROUND_IMAGE)



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

# ────────────────────────────────────────────────────────────────────────────
# Global background
if background:
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image:
                linear-gradient(
                    rgba(7, 10, 18, 0.82),
                    rgba(7, 10, 18, 0.90)
                ),
                url("data:image/jpeg;base64,{background}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stSidebar"] {{
            background: rgba(8, 11, 20, 0.94);
        }}

        .stMarkdown,
        .stText,
        h1, h2, h3, h4, h5, h6,
        p, li, label {{
            color: white;
        }}

        .stButton > button {{
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.16);
            background: rgba(255,255,255,0.04);
            color: white;
            font-weight: 600;
        }}

        .stButton > button:hover {{
            background: rgba(255,255,255,0.09);
            border-color: rgba(255,255,255,0.28);
            color: white;
        }}

        div[data-baseweb="select"] > div {{
            border-radius: 10px;
            border-color: rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.05);
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
        }}

        [data-testid="stExpander"] {{
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.025);
        }}

        hr {{
            border-color: rgba(255,255,255,0.10);
        }}

        /* Main content cards */

        .home-section-card {{
            padding: 24px 26px;
            margin: 0 0 18px 0;

            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 14px;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.050),
                    rgba(255,255,255,0.018)
                );

            box-shadow:
                0 10px 30px rgba(0,0,0,0.16),
                inset 0 1px 0 rgba(255,255,255,0.025);

            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
        }}

        .home-section-card h3 {{
            margin-top: 0;
            margin-bottom: 12px;
        }}

        .home-section-card p {{
            margin-bottom: 10px;
        }}

        .home-section-card ul {{
            margin-bottom: 0;
        }}

        .metric-card {{
            padding: 18px 20px;
            min-height: 112px;

            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 13px;

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.045),
                    rgba(255,255,255,0.015)
                );

            box-shadow:
                0 8px 24px rgba(0,0,0,0.13),
                inset 0 1px 0 rgba(255,255,255,0.025);

            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
        }}

        .metric-card-label {{
            color: rgba(255,255,255,0.72);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.3px;
        }}

        .metric-card-value {{
            margin-top: 7px;
            color: #ffffff;
            font-size: 30px;
            font-weight: 800;
            line-height: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Database
if init_schema:
    init_schema()


# ────────────────────────────────────────────────────────────────────────────
# Main header
# ────────────────────────────────────────────────────────────────────────────
if header:
    st.markdown(
        f"""
        <style>
        .cricbuzz-header {{
            min-height: 280px;
            padding: 50px 60px;
            margin-bottom: 30px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border-radius: 24px;
            background-image:
                linear-gradient(
                    110deg,
                    rgba(4, 7, 15, 0.90),
                    rgba(4, 7, 15, 0.45),
                    rgba(4, 7, 15, 0.80)
                ),
                url("data:image/jpeg;base64,{header}");
            background-size: cover;
            background-position: center;
            border: 1px solid rgba(255,255,255,0.14);
            box-shadow: 0 15px 45px rgba(0,0,0,0.35);
        }}
        .cricbuzz-badge {{
            width: fit-content;
            padding: 7px 15px;
            margin-bottom: 15px;
            border-radius: 30px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.18);
            color: rgba(255,255,255,0.9);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 1.5px;
        }}
        .cricbuzz-title {{
            margin: 0;
            color: white;
            font-size: 48px;
            font-weight: 900;
            text-shadow: 0 4px 18px rgba(0,0,0,0.65);
        }}
        .cricbuzz-subtitle {{
            margin-top: 12px;
            color: rgba(255,255,255,0.90);
            font-size: 19px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.7);
        }}
        .cricbuzz-tagline {{
            margin-top: 18px;
            color: rgba(255,255,255,0.65);
            font-size: 13px;
            letter-spacing: 1px;
        }}
        </style>

        <div class="cricbuzz-header">
            <div class="cricbuzz-badge">🏏 CRICBUZZ LIVESTATS • CRICKET ANALYTICS ARENA</div>
            <h1 class="cricbuzz-title">Cricbuzz LiveStats</h1>
            <div class="cricbuzz-subtitle">Real-Time Cricket Insights & SQL-Based Analytics</div>
            <div class="cricbuzz-tagline">
                📊 LIVE DATA &nbsp; • &nbsp;
                🧠 SQL ANALYTICS &nbsp; • &nbsp;
                🏆 PLAYER PERFORMANCE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.title("🏏 Cricbuzz LiveStats")
    st.subheader("Real-Time Cricket Insights & SQL-Based Analytics")


# ────────────────────────────────────────────────────────────────────────────
# Sidebar: Project overview

with st.sidebar:

    st.markdown("## 📊 Project Overview")

    st.caption(
        "Cricbuzz LiveStats is a cricket analytics dashboard "
        "combining live data, player statistics, SQL analysis "
        "and roster management."
    )

    st.markdown("---")

    # Project status

    st.markdown("#### Project Status")

    status_col1, status_col2 = st.columns(2)

    with status_col1:
        st.metric(
            "Analytics",
            "25",
        )

    with status_col2:
        st.metric(
            "Live Cricket",
            "ON",
        )

    st.markdown("---")

    # Data sources

    st.markdown("#### Data Sources")

    st.write("🟢 **Cricbuzz API**")
    st.caption("Live scores and player rankings")

    st.write("🟢 **SQLite Database**")
    st.caption("Historical statistics and analytics")

    st.write("🟢 **SQL Analytics**")
    st.caption("25 cricket questions")

    st.markdown("---")

    # Navigation guide

    st.markdown("#### Explore")

    st.caption(
        "Use the navigation above to move between "
        "the live cricket dashboard, player statistics, "
        "SQL analytics and roster management."
    )

    st.markdown("---")

    st.caption(
        "🏏 Cricbuzz LiveStats"
    )


# ────────────────────────────────────────────────────────────────────────────
# Home intro

# Home introduction

with st.container(border=True):

    st.markdown("### Explore Cricbuzz LiveStats")

    st.markdown(
        """
        Welcome to **Cricbuzz LiveStats** — an interactive cricket analytics
        platform combining live match data, player statistics, SQL analysis,
        and roster management.
        """
    )

    st.markdown(
        """
        - 🏠 **Home** — project overview and key metrics
        - 🔴 **Live Matches** — follow live cricket scores and match updates
        - 🏆 **Cricket Rankings & Fantasy** — explore batting and bowling leaderboards
        - 🧠 **SQL Queries & Analytics** — explore all 25 cricket analytics questions
        - 🛠️ **CRUD Operations** — add, edit and manage player records
        """
    )


# Project metrics

st.markdown("")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.markdown("🏏 **Analytics Queries**")
        st.markdown("## 25")
        st.caption("Practice SQL analytics questions")


with c2:
    with st.container(border=True):
        st.markdown("📊 **SQL Powered**")
        st.markdown("## 100%")
        st.caption("Analytics backed by SQL queries")


with c3:
    with st.container(border=True):
        st.markdown("⚡ **Live Cricket**")
        st.markdown("## Enabled")
        st.caption("Live match data available")


# Make Streamlit bordered containers match the Cricbuzz glass-card design.
# This applies only to bordered containers, so normal page content remains
# unaffected.

st.markdown(
    """
    <style>

    /* Main translucent section cards */

    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 14px !important;

        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.050),
                rgba(255,255,255,0.018)
            ) !important;

        box-shadow:
            0 10px 30px rgba(0,0,0,0.16),
            inset 0 1px 0 rgba(255,255,255,0.025) !important;

        backdrop-filter: blur(3px);
        -webkit-backdrop-filter: blur(3px);
    }

    [data-testid="stVerticalBlockBorderWrapper"] h3 {
        margin-top: 0 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMetric"] {
        background: transparent !important;
        border: none !important;
        padding: 4px 0 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)
