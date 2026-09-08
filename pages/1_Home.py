import sys
from pathlib import Path

import streamlit as st


# Project root

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from utils.theme import apply_theme


# Page configuration

st.set_page_config(
    page_title="Home | Cricbuzz LiveStats",
    page_icon="🏠",
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
        box-shadow: 0 5px 16px rgba(0,0,0,0.18) !important;
    }

    [data-testid="stSidebarNav"] a:hover::before {
        background: rgba(180,185,255,0.70) !important;
        box-shadow: 0 0 7px rgba(160,165,255,0.45) !important;
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
        box-shadow: 0 0 9px rgba(170,175,255,0.85) !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"]:hover {
        transform: translateX(1px) !important;
        border-color: rgba(160,165,255,0.48) !important;
    }


    /* Sidebar information */

    .home-sidebar-title {
        margin: 18px 4px 8px 4px;
        color: rgba(255,255,255,0.88);
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(255,255,255,0.08) !important;
        background: rgba(255,255,255,0.025) !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 3px !important;
        color: rgba(255,255,255,0.86);
        font-size: 10px;
    }

    [data-testid="stSidebar"] .stCaption {
        margin-top: 0 !important;
        margin-bottom: 7px !important;
        color: rgba(255,255,255,0.50) !important;
        font-size: 9px !important;
        line-height: 1.35 !important;
    }

    .home-sidebar-author-label {
        color: rgba(255,255,255,0.38);
        font-size: 8px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .home-sidebar-footer {
        margin: 14px 4px 0 4px;
        padding-top: 12px;
        border-top: 1px solid rgba(255,255,255,0.09);
        color: rgba(255,255,255,0.25);
        font-size: 8px;
        font-weight: 800;
        letter-spacing: 1.5px;
    }


    /* Main page sections */

    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid rgba(255,255,255,0.085) !important;
        border-radius: 13px !important;
        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.045),
                rgba(255,255,255,0.018)
            ) !important;
        box-shadow:
            0 8px 28px rgba(0,0,0,0.14),
            inset 0 1px 0 rgba(255,255,255,0.025) !important;
    }

    .home-section-label {
        color: rgba(190,195,255,0.78);
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 1.3px;
        text-transform: uppercase;
        margin-bottom: 3px;
    }

    .home-section-note {
        color: rgba(255,255,255,0.48);
        font-size: 11px;
        line-height: 1.5;
    }

    .home-author-name {
        color: #ffffff;
        font-size: 17px;
        font-weight: 800;
        margin-top: 3px;
    }

    .home-author-role {
        color: rgba(255,255,255,0.48);
        font-size: 10px;
        margin-top: 4px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# Cricbuzz theme

apply_theme(
    badge_text="🏠 HOME • CRICKET ANALYTICS ARENA",
    title="Home",
    subtitle="Project overview, tools, and setup",
    tagline=(
        "🐍 PYTHON &nbsp; • &nbsp; "
        "🗄️ SQLITE &nbsp; • &nbsp; "
        "🔌 REST API &nbsp; • &nbsp; "
        "🐼 PANDAS"
    ),
)


# Header styling

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


# Sidebar information

with st.sidebar:

    st.markdown(
        '<div class="home-sidebar-title">Project Overview</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        st.markdown("🏏 **Live Cricket**")
        st.caption(
            "Real-time match data through the Cricbuzz API."
        )

        st.markdown("📊 **Cricket Rankings & Fantasy**")
        st.caption(
            "Rankings, ratings, points, and player performance."
        )

        st.markdown("🔎 **SQL Analytics**")
        st.caption(
            "25 practice queries from beginner to advanced."
        )

        st.markdown("🛠️ **CRUD Management**")
        st.caption(
            "Manage player records in the local database."
        )

    st.markdown(
        '<div class="home-sidebar-title">Tech Stack</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        st.markdown("🐍 **Python**")
        st.markdown("🎨 **Streamlit**")
        st.markdown("🗄️ **SQLite**")
        st.markdown("🔌 **REST API**")
        st.markdown("🐼 **pandas**")

    with st.container(border=True):

        st.markdown(
            '<div class="home-sidebar-author-label">Project Author</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**Kartikey Singh**")

    st.markdown(
        '<div class="home-sidebar-footer">CRICBUZZ LIVESTATS</div>',
        unsafe_allow_html=True,
    )


# Project overview

with st.container(border=True):

    st.markdown(
        '<div class="home-section-label">Project Overview</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## About this project")

    st.markdown(
        """
        **Cricbuzz LiveStats** is a cricket analytics dashboard combining:

        - Live match data from the Cricbuzz API with local and persistent GitHub-backed caching
        - A local SQL database seeded from historical stats datasets
        - 25 practice SQL queries spanning beginner → advanced analytics
        - Full CRUD tooling for managing player records
        """
    )


st.write("")


# Tools used

with st.container(border=True):

    st.markdown(
        '<div class="home-section-label">Technology</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Tools used")

    st.markdown(
        """
        Python · Streamlit · SQLite (swappable for PostgreSQL/MySQL) ·
        REST API · pandas
        """
    )


st.write("")


# Folder structure

with st.container(border=True):

    st.markdown(
        '<div class="home-section-label">Architecture</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Folder structure")

    st.code(
        """cricbuzz_livestats/
├── app.py
├── requirements.txt
├── pages/
│   ├── 1_Home.py
│   ├── 2_Live_Matches.py
│   ├── 3_Cricket_Rankings_&_Fantasy.py
│   ├── 4_SQL_Queries_Analytics.py
│   └── 5_CRUD_Operations.py
├── utils/
│   ├── db_connection.py
│   ├── gamification.py
│   ├── theme.py
│   └── api_helper.py
├── sql_queries/
│   └── queries.py
├── data/
│   ├── api_cache/
│   ├── Images/
│   │   ├── IND Players/
│   │   ├── background.jpg
│   │   ├── header.jpg
│   │   └── Indian Flag.png
│   ├── cricbuzz_livestats.db
│   ├── ingest_cricsheet.py
│   ├── ingest_players_from_csv.py
│   └── schema.sql
├── .gitignore
└── README.md""",
        language="text",
    )


st.write("")


# Setup

with st.container(border=True):

    st.markdown(
        '<div class="home-section-label">Getting Started</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Setup")

    st.markdown(
        """
        1. `pip install -r requirements.txt`
        2. Copy `.env.example` to `.env` and add your Cricbuzz API and GitHub cache settings
        3. Run the required historical data ingestion scripts if the database needs to be rebuilt
        4. Keep `data/api_cache/` available for persistent API cache files
        5. `streamlit run app.py`
        """
    )


st.write("")


# Project author

with st.container(border=True):

    st.markdown(
        '<div class="home-section-label">Project Author</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-author-name">Kartikey Singh</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="home-author-role">Cricket Analytics • Python • SQL • Streamlit</div>',
        unsafe_allow_html=True,
    )
