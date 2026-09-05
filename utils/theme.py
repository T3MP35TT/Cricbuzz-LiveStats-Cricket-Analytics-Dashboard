"""
Shared visual theme for Cricbuzz LiveStats.

Call apply_theme(...) once near the top of every page, right after
st.set_page_config(), so the dark background, hero header banner, and
shared component styles look identical everywhere.
"""

import base64
from pathlib import Path

import streamlit as st


# Project paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "Images"

HEADER_IMAGE = IMAGE_DIR / "header.jpg"
BACKGROUND_IMAGE = IMAGE_DIR / "background.jpg"

DEFAULT_BADGE_TEXT = "🏏 CRICBUZZ LIVESTATS • CRICKET ANALYTICS ARENA"


def _encode_image(path):
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode()


def _inject_background_and_component_styles(background_b64):
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image:
                linear-gradient(
                    rgba(7, 10, 18, 0.82),
                    rgba(7, 10, 18, 0.90)
                ),
                url("data:image/jpeg;base64,{background_b64}");
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

        .stMarkdown, .stText,
        h1, h2, h3, h4, h5, h6,
        p, li, label {{
            color: white;
        }}

        .game-card {{
            padding: 18px 20px;
            border-radius: 16px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.12);
            margin-bottom: 14px;
        }}

        .badge-chip {{
            display: inline-block;
            padding: 8px 14px;
            margin: 4px 6px 4px 0;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 700;
        }}

        .badge-unlocked {{
            background: rgba(255, 200, 60, 0.18);
            border: 1px solid rgba(255, 200, 60, 0.55);
            color: #ffd76a;
        }}

        .badge-locked {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.10);
            color: rgba(255,255,255,0.35);
        }}

        .mission-title {{
            font-size: 17px;
            font-weight: 800;
            color: white;
        }}

        .mission-desc {{
            font-size: 13px;
            color: rgba(255,255,255,0.65);
            margin-bottom: 10px;
        }}

        .xp-tag {{
            font-size: 12px;
            font-weight: 700;
            color: #7ee787;
        }}

        .predict-chip {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            background: rgba(255, 200, 60, 0.18);
            border: 1px solid rgba(255, 200, 60, 0.55);
            color: #ffd76a;
        }}

        .hot-chip {{
            display: inline-block;
            padding: 4px 12px;
            margin-left: 6px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            background: rgba(255, 90, 90, 0.18);
            border: 1px solid rgba(255, 90, 90, 0.55);
            color: #ff8080;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_hero_header(header_b64, badge_text, title, subtitle, tagline):
    tagline_html = (
        f'<div class="cricbuzz-tagline">{tagline}</div>'
        if tagline
        else ""
    )

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
                url("data:image/jpeg;base64,{header_b64}");
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
            <div class="cricbuzz-badge">{badge_text}</div>
            <h1 class="cricbuzz-title">{title}</h1>
            <div class="cricbuzz-subtitle">{subtitle}</div>
            {tagline_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_theme(
    title,
    subtitle,
    tagline=None,
    badge_text=DEFAULT_BADGE_TEXT,
):
    """
    Apply the shared theme to the current Streamlit page.

    This function intentionally remains available at module level because
    every page imports it with:

        from utils.theme import apply_theme
    """
    background_b64 = _encode_image(BACKGROUND_IMAGE)
    header_b64 = _encode_image(HEADER_IMAGE)

    if background_b64:
        _inject_background_and_component_styles(background_b64)

    if header_b64:
        _inject_hero_header(
            header_b64,
            badge_text,
            title,
            subtitle,
            tagline,
        )
    else:
        st.title(title)
        if subtitle:
            st.subheader(subtitle)
