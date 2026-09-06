import streamlit as st
import pandas as pd

from utils.db_connection import run_query, execute_write
from utils.theme import apply_theme


# Page configuration

st.set_page_config(
    page_title="CRUD Operations | Cricbuzz LiveStats",
    page_icon="🛠",
    layout="wide"
)


# Cricbuzz theme

apply_theme(
    title="🛠 CRUD Operations — Player Records",
    subtitle="Create, read, update, and manage player records in the local database.",
    tagline="🛠️ MANAGE PLAYERS • 🗂️ KEEP DATA CLEAN • 🏏 CONTROL YOUR CRICKET DATA",
)


# Sidebar and CRUD styling

st.markdown(
    """
    <style>

    /* Page typography */

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


    /* Sidebar */

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
        padding: 18px 12px 12px 12px !important;
    }

    [data-testid="stSidebarNav"] ul {
        padding: 0 !important;
        margin: 0 !important;
        gap: 4px !important;
    }

    [data-testid="stSidebarNav"] li {
        padding: 0 !important;
        margin: 0 !important;
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

        background: rgba(255,255,255,0.055) !important;
        border-color: rgba(255,255,255,0.08) !important;

        transform: translateX(1px) !important;

        box-shadow:
            0 5px 16px rgba(0,0,0,0.18) !important;
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


    /* Sidebar information */

    .sidebar-section-title {
        margin: 18px 4px 8px 4px;

        color: rgba(255,255,255,0.88);

        font-size: 10px;
        font-weight: 800;

        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    [data-testid="stSidebar"] [data-testid="stMetric"] {
        padding: 9px 9px 7px 9px !important;

        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 9px !important;

        background: rgba(255,255,255,0.035) !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.42) !important;

        font-size: 8px !important;
        font-weight: 700 !important;

        text-transform: uppercase !important;
        letter-spacing: 0.7px !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #ffffff !important;

        font-size: 17px !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetricDelta"] {
        display: none !important;
    }

    [data-testid="stSidebar"] .stCaption {
        color: rgba(255,255,255,0.52) !important;
        font-size: 9px !important;
    }

    [data-testid="stSidebar"] .stCaption strong {
        color: rgba(255,255,255,0.86) !important;
    }

    .sidebar-footer {
        margin-top: 14px;
        padding-top: 12px;

        border-top: 1px solid rgba(255,255,255,0.08);

        color: rgba(255,255,255,0.25);

        font-size: 8px;
        font-weight: 800;

        letter-spacing: 1.5px;
        text-align: left;
    }


    /* CRUD tabs */

    div[data-baseweb="tab-list"] {
        gap: 3px !important;

        padding: 5px !important;

        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;

        background: rgba(255,255,255,0.025) !important;
    }

    button[data-baseweb="tab"] {
        min-height: 42px !important;

        padding: 0 18px !important;

        border-radius: 9px !important;

        color: rgba(255,255,255,0.58) !important;

        font-size: 13px !important;
        font-weight: 700 !important;

        border: 1px solid transparent !important;

        transition:
            background 0.18s ease,
            color 0.18s ease,
            border-color 0.18s ease !important;
    }

    button[data-baseweb="tab"]:hover {
        color: #ffffff !important;
        background: rgba(255,255,255,0.055) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;

        background:
            linear-gradient(
                90deg,
                rgba(120,126,255,0.23),
                rgba(115,120,220,0.11)
            ) !important;

        border-color: rgba(145,150,255,0.34) !important;

        box-shadow:
            0 4px 14px rgba(0,0,0,0.18) !important;
    }

    div[data-baseweb="tab-highlight"] {
        background-color: rgba(190,195,255,0.95) !important;
        height: 2px !important;
    }


    /* Section headers */

    .crud-section {
        margin-top: 18px;
        margin-bottom: 12px;
    }

    .crud-kicker {
        color: rgba(190,195,255,0.80);

        font-size: 10px;
        font-weight: 800;

        letter-spacing: 1.4px;
        text-transform: uppercase;
    }

    .crud-description {
        margin-top: 4px;

        color: rgba(255,255,255,0.48);

        font-size: 11px;
        line-height: 1.5;
    }


    /* Form presentation */

    .crud-form-note {
        margin-bottom: 12px;
        padding: 10px 12px;

        border-left: 3px solid rgba(175,180,255,0.85);
        border-radius: 7px;

        background: rgba(120,126,255,0.07);

        color: rgba(255,255,255,0.58);

        font-size: 11px;
        line-height: 1.45;
    }


    /* Read metrics */

    .record-metric {
        padding: 13px 14px;

        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 11px;

        background: rgba(255,255,255,0.025);
    }

    .record-metric-value {
        color: #ffffff;

        font-size: 21px;
        font-weight: 800;
    }

    .record-metric-label {
        margin-top: 2px;

        color: rgba(255,255,255,0.40);

        font-size: 9px;
        font-weight: 700;

        letter-spacing: 0.7px;
        text-transform: uppercase;
    }


    /* Dataframe container */

    [data-testid="stDataFrame"] {
        margin-top: 8px !important;

        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 11px !important;

        overflow: hidden !important;

        box-shadow:
            0 8px 24px rgba(0,0,0,0.14) !important;
    }


    /* Buttons */

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 8px !important;

        border: 1px solid rgba(255,255,255,0.13) !important;

        font-weight: 700 !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: rgba(175,180,255,0.50) !important;

        box-shadow:
            0 5px 14px rgba(0,0,0,0.20) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# Sidebar data

try:
    sidebar_stats = run_query(
        """
        SELECT
            COUNT(*) AS total_players,
            SUM(
                CASE
                    WHEN admin_active = 1 THEN 1
                    ELSE 0
                END
            ) AS active_players,
            COUNT(DISTINCT country) AS countries,
            COUNT(DISTINCT playing_role) AS roles
        FROM players
        """
    )

    sidebar_recent = run_query(
        """
        SELECT
            player_name,
            country
        FROM players
        WHERE admin_active = 1
        ORDER BY player_id DESC
        LIMIT 3
        """
    )

except Exception:
    sidebar_stats = pd.DataFrame(
        [{
            "total_players": 0,
            "active_players": 0,
            "countries": 0,
            "roles": 0,
        }]
    )

    sidebar_recent = pd.DataFrame()


total_players = int(
    sidebar_stats.iloc[0]["total_players"] or 0
)

active_players = int(
    sidebar_stats.iloc[0]["active_players"] or 0
)

countries = int(
    sidebar_stats.iloc[0]["countries"] or 0
)

roles = int(
    sidebar_stats.iloc[0]["roles"] or 0
)


with st.sidebar:

    st.markdown(
        '<div class="sidebar-section-title">Player Database</div>',
        unsafe_allow_html=True,
    )

    stat_col1, stat_col2 = st.columns(2)

    with stat_col1:
        st.metric(
            "Players",
            f"{total_players:,}",
        )

    with stat_col2:
        st.metric(
            "Active",
            f"{active_players:,}",
        )

    stat_col3, stat_col4 = st.columns(2)

    with stat_col3:
        st.metric(
            "Countries",
            f"{countries:,}",
        )

    with stat_col4:
        st.metric(
            "Roles",
            f"{roles:,}",
        )


    st.markdown(
        '<div class="sidebar-section-title">Quick Guide</div>',
        unsafe_allow_html=True,
    )

    guide_col1, guide_col2 = st.columns(2)

    with guide_col1:
        st.caption("➕ **Create**")
        st.caption("Add player")

    with guide_col2:
        st.caption("👁 **Read**")
        st.caption("Browse records")

    guide_col3, guide_col4 = st.columns(2)

    with guide_col3:
        st.caption("✏️ **Update**")
        st.caption("Edit details")

    with guide_col4:
        st.caption("🗑 **Delete**")
        st.caption("Remove record")


    if not sidebar_recent.empty:

        st.markdown(
            '<div class="sidebar-section-title">Recently Added</div>',
            unsafe_allow_html=True,
        )

        for _, row in sidebar_recent.iterrows():

            player_name = str(
                row["player_name"]
            )

            player_country = str(
                row["country"] or "Unknown"
            )

            recent_col1, recent_col2 = st.columns(
                [1.35, 1]
            )

            with recent_col1:
                st.caption(
                    f"🏏 {player_name}"
                )

            with recent_col2:
                st.caption(
                    player_country
                )


    st.markdown(
        '<div class="sidebar-footer">CRICBUZZ LIVESTATS</div>',
        unsafe_allow_html=True,
    )


# CRUD navigation

tab_create, tab_read, tab_update, tab_delete = st.tabs(
    [
        "➕  Create",
        "👁  Read",
        "✏️  Update",
        "🗑  Delete",
    ]
)


# Create player

with tab_create:

    st.markdown(
        """
        <div class="crud-section">
            <div class="crud-kicker">Player Management</div>
            <h2 style="margin: 3px 0 0 0;">Add a new player</h2>
            <div class="crud-description">
                Create a player record and add their core cricket profile
                information to the local database.
            </div>
        </div>

        <div class="crud-form-note">
            Enter the player's basic identity, playing role, batting style,
            and bowling style. Player name is required.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("create_player", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Player name",
                placeholder="e.g. Virat Kohli",
            )

        with col2:
            country = st.text_input(
                "Country",
                placeholder="e.g. India",
            )

        col3, col4 = st.columns(2)

        with col3:
            role = st.selectbox(
                "Playing role",
                [
                    "Batsman",
                    "Bowler",
                    "All-rounder",
                    "Wicket-keeper",
                ],
            )

        with col4:
            bat_style = st.text_input(
                "Batting style",
                "Right-hand bat",
            )

        bowl_style = st.text_input(
            "Bowling style",
            "",
            placeholder="e.g. Right-arm fast, Left-arm orthodox, Does not bowl",
        )

        submitted = st.form_submit_button(
            "➕ Add player",
            use_container_width=False,
        )

        if submitted:

            if not name.strip():
                st.error("Player name is required.")

            else:
                try:
                    execute_write(
                        """
                        INSERT INTO players (
                            player_name,
                            country,
                            playing_role,
                            batting_style,
                            bowling_style
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            name.strip(),
                            country.strip(),
                            role,
                            bat_style.strip(),
                            bowl_style.strip(),
                        ),
                    )

                    st.success(
                        f"Added **{name.strip()}** successfully."
                    )

                    st.rerun()

                except Exception as e:
                    st.error(
                        f"Could not add player: {e}"
                    )


# Read players

with tab_read:

    st.markdown(
        """
        <div class="crud-section">
            <div class="crud-kicker">Database Explorer</div>
            <h2 style="margin: 3px 0 0 0;">Active players</h2>
            <div class="crud-description">
                Search, inspect, and explore active player records stored
                in the database.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    search_col, clear_col = st.columns([5, 1])

    with search_col:
        search = st.text_input(
            "Filter by name or country",
            placeholder="Search player name or country...",
            label_visibility="visible",
        )

    with clear_col:
        st.write("")
        st.write("")
        if st.button(
            "Clear",
            use_container_width=True,
            key="clear_player_search",
        ):
            st.session_state["player_read_search"] = ""
            st.rerun()

    if search:
        df = run_query(
            """
            SELECT
                player_id,
                player_name,
                country,
                playing_role,
                batting_style,
                bowling_style,
                real_name,
                admin_active
            FROM players
            WHERE admin_active = 1
              AND (
                    player_name LIKE ?
                    OR country LIKE ?
                  )
            ORDER BY player_name
            """,
            (
                f"%{search}%",
                f"%{search}%",
            ),
        )

    else:
        df = run_query(
            """
            SELECT
                player_id,
                player_name,
                country,
                playing_role,
                batting_style,
                bowling_style,
                real_name,
                admin_active
            FROM players
            WHERE admin_active = 1
            ORDER BY player_name
            """
        )

    active_count = len(df)

    country_count = (
        int(df["country"].nunique())
        if not df.empty and "country" in df.columns
        else 0
    )

    role_count = (
        int(df["playing_role"].nunique())
        if not df.empty and "playing_role" in df.columns
        else 0
    )

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.markdown(
            f"""
            <div class="record-metric">
                <div class="record-metric-value">{active_count:,}</div>
                <div class="record-metric-label">Matching players</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with metric2:
        st.markdown(
            f"""
            <div class="record-metric">
                <div class="record-metric-value">{country_count:,}</div>
                <div class="record-metric-label">Countries</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with metric3:
        st.markdown(
            f"""
            <div class="record-metric">
                <div class="record-metric-value">{role_count:,}</div>
                <div class="record-metric-label">Playing roles</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    if df.empty:
        st.info(
            "No active players match your search."
        )

    else:

        display_df = df.copy()

        display_df.columns = [
            "Player ID",
            "Player Name",
            "Country",
            "Playing Role",
            "Batting Style",
            "Bowling Style",
            "Real Name",
            "Status",
        ]

        display_df["Status"] = display_df["Status"].map(
            {
                1: "Active",
                0: "Inactive",
            }
        ).fillna("Unknown")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=min(
                520,
                max(260, 42 + (len(display_df) * 35)),
            ),
            column_config={
                "Player ID": st.column_config.NumberColumn(
                    "ID",
                    width="small",
                    format="%d",
                ),
                "Player Name": st.column_config.TextColumn(
                    "PLAYER",
                    width="medium",
                ),
                "Country": st.column_config.TextColumn(
                    "COUNTRY",
                    width="medium",
                ),
                "Playing Role": st.column_config.TextColumn(
                    "ROLE",
                    width="medium",
                ),
                "Batting Style": st.column_config.TextColumn(
                    "BATTING STYLE",
                    width="medium",
                ),
                "Bowling Style": st.column_config.TextColumn(
                    "BOWLING STYLE",
                    width="large",
                ),
                "Real Name": st.column_config.TextColumn(
                    "REAL NAME",
                    width="medium",
                ),
                "Status": st.column_config.TextColumn(
                    "STATUS",
                    width="small",
                ),
            },
        )


# Update player

with tab_update:

    st.markdown(
        """
        <div class="crud-section">
            <div class="crud-kicker">Player Management</div>
            <h2 style="margin: 3px 0 0 0;">Edit a player</h2>
            <div class="crud-description">
                Select an existing player and update their profile
                information without changing their player ID.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    players_df = run_query(
        """
        SELECT player_id, player_name
        FROM players
        WHERE admin_active = 1
        ORDER BY player_name
        """
    )

    if players_df.empty:

        st.info(
            "No active players yet — add one in the Create tab."
        )

    else:

        options = dict(
            zip(
                players_df["player_name"],
                players_df["player_id"],
            )
        )

        selected_name = st.selectbox(
            "Select player to edit",
            list(options.keys()),
            key="update_player_select",
        )

        pid = options[selected_name]

        current_df = run_query(
            """
            SELECT *
            FROM players
            WHERE player_id = ?
            """,
            (pid,),
        )

        if current_df.empty:

            st.error(
                "The selected player could not be found."
            )

        else:

            current = current_df.iloc[0]

            st.markdown(
                f"""
                <div class="crud-form-note">
                    Editing <strong>{selected_name}</strong>
                    &nbsp;•&nbsp; Player ID: <strong>{pid}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("update_player"):

                col1, col2 = st.columns(2)

                with col1:
                    new_country = st.text_input(
                        "Country",
                        current["country"] or "",
                    )

                with col2:

                    role_options = [
                        "Batsman",
                        "Bowler",
                        "All-rounder",
                        "Wicket-keeper",
                    ]

                    current_role = current["playing_role"]

                    role_index = (
                        role_options.index(current_role)
                        if current_role in role_options
                        else 0
                    )

                    new_role = st.selectbox(
                        "Playing role",
                        role_options,
                        index=role_index,
                    )

                new_bat_style = st.text_input(
                    "Batting style",
                    current["batting_style"] or "",
                )

                new_bowl_style = st.text_input(
                    "Bowling style",
                    current["bowling_style"] or "",
                )

                save_changes = st.form_submit_button(
                    "💾 Save changes",
                )

                if save_changes:

                    try:

                        execute_write(
                            """
                            UPDATE players
                            SET
                                country = ?,
                                playing_role = ?,
                                batting_style = ?,
                                bowling_style = ?
                            WHERE player_id = ?
                            """,
                            (
                                new_country.strip(),
                                new_role,
                                new_bat_style.strip(),
                                new_bowl_style.strip(),
                                pid,
                            ),
                        )

                        st.success(
                            f"{selected_name} was updated successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Could not update player: {e}"
                        )


# Delete player

with tab_delete:

    st.markdown(
        """
        <div class="crud-section">
            <div class="crud-kicker">Database Maintenance</div>
            <h2 style="margin: 3px 0 0 0;">Remove a player</h2>
            <div class="crud-description">
                Permanently remove an active player record from the local
                database. Confirmation is required before deletion.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    players_df = run_query(
        """
        SELECT player_id, player_name, country, playing_role
        FROM players
        WHERE admin_active = 1
        ORDER BY player_name
        """
    )

    if players_df.empty:

        st.info(
            "No active players available for deletion."
        )

    else:

        options = dict(
            zip(
                players_df["player_name"],
                players_df["player_id"],
            )
        )

        selected_name = st.selectbox(
            "Select player to delete",
            list(options.keys()),
            key="delete_select",
        )

        pid = options[selected_name]

        selected_row = players_df[
            players_df["player_id"] == pid
        ].iloc[0]

        st.markdown(
            f"""
            <div class="crud-form-note">
                <strong>{selected_name}</strong>
                &nbsp;•&nbsp;
                {selected_row["country"] or "Unknown country"}
                &nbsp;•&nbsp;
                {selected_row["playing_role"] or "Unknown role"}
            </div>
            """,
            unsafe_allow_html=True,
        )

        confirm = st.checkbox(
            f"I confirm I want to permanently delete {selected_name}.",
            key="delete_confirmation",
        )

        if st.button(
            "🗑 Delete player",
            type="primary",
            disabled=not confirm,
            key="delete_player_button",
        ):

            try:

                execute_write(
                    """
                    DELETE FROM players
                    WHERE player_id = ?
                    """,
                    (pid,),
                )

                st.success(
                    f"Deleted {selected_name} successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not delete player: {e}"
                )
