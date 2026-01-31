from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    theme = st.session_state.get("ui_theme", "light")

    if theme == "dark":
        # Dark theme colors
        bg_color = "#0E1117"
        secondary_bg = "#262730"
        text_color = "#FAFAFA"
        card_border = "#334155"
        card_bg = "#1E1E1E"
        muted_text = "#94A3B8"
        surface_bg = "#111827"
        citation_bg = "#0B1220"
        citation_text = "#E2E8F0"
        shadow = "0 1px 2px rgba(2, 6, 23, 0.6)"
        primary_color = "#2F80ED"
        hover_bg = "#2D2D2D"
    else:
        # Light theme colors
        bg_color = "#FFFFFF"
        secondary_bg = "#F0F2F6"
        text_color = "#31333F"
        card_border = "#E2E8F0"
        card_bg = "#FFFFFF"
        muted_text = "#64748B"
        surface_bg = "#F8FAFC"
        citation_bg = "#0F172A"
        citation_text = "#F8FAFC"
        shadow = "0 1px 2px rgba(15, 23, 42, 0.04)"
        primary_color = "#2F80ED"
        hover_bg = "#F0F2F6"

    st.markdown(
        f"""
        <style>
        :root {{
          --card-border: {card_border};
          --card-bg: {card_bg};
          --muted-text: {muted_text};
          --surface-bg: {surface_bg};
          --citation-bg: {citation_bg};
          --citation-text: {citation_text};
          --bg-color: {bg_color};
          --text-color: {text_color};
          --secondary-bg: {secondary_bg};
          --primary-color: {primary_color};
        }}

        /* Main app background */
        .stApp {{
          background-color: {bg_color};
        }}

        /* Main content area */
        .main .block-container {{
          background-color: {bg_color};
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
          background-color: {secondary_bg};
        }}

        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] label {{
          color: {text_color};
        }}

        /* Text elements */
        .stMarkdown, .stCaption, p, span, label {{
          color: {text_color};
        }}

        h1, h2, h3, h4, h5, h6 {{
          color: {text_color};
        }}

        /* Buttons */
        .stButton > button {{
          background-color: {secondary_bg};
          color: {text_color};
          border-color: {card_border};
        }}

        .stButton > button:hover {{
          background-color: {hover_bg};
          border-color: {primary_color};
        }}

        .stButton > button[kind="primary"] {{
          background-color: {primary_color};
          color: white;
        }}

        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {{
          background-color: {card_bg};
          color: {text_color};
          border-color: {card_border};
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
          background-color: {secondary_bg};
          color: {text_color};
        }}

        .streamlit-expanderContent {{
          background-color: {card_bg};
        }}

        /* Metrics */
        [data-testid="stMetricValue"] {{
          color: {text_color};
        }}

        [data-testid="stMetricLabel"] {{
          color: {muted_text};
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
          background-color: {secondary_bg};
        }}

        .stTabs [data-baseweb="tab"] {{
          color: {text_color};
        }}

        /* Custom card styles */
        .sf-card {{
          border: 1px solid var(--card-border);
          background: var(--card-bg);
          border-radius: 12px;
          padding: 16px;
          box-shadow: {shadow};
          margin-bottom: 16px;
          transition: box-shadow 0.2s ease, transform 0.2s ease;
        }}
        .sf-card:hover {{
          transform: translateY(-1px);
          box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
        }}
        .sf-muted {{
          color: var(--muted-text);
        }}
        .sf-section-title {{
          font-size: 1.05rem;
          font-weight: 600;
          margin-bottom: 6px;
        }}
        .sf-chip {{
          display: inline-block;
          padding: 2px 8px;
          border-radius: 999px;
          border: 1px solid var(--card-border);
          background: var(--surface-bg);
          margin-right: 6px;
          font-size: 0.8rem;
        }}
        .sf-divider {{
          border-top: 1px solid var(--card-border);
          margin: 12px 0;
        }}
        .sf-citation {{
          position: relative;
          cursor: help;
          border-bottom: 1px dashed var(--muted-text);
          padding: 0 2px;
        }}
        .sf-citation::after {{
          content: attr(data-tooltip);
          position: absolute;
          left: 0;
          bottom: 120%;
          min-width: 240px;
          max-width: 420px;
          background: var(--citation-bg);
          color: var(--citation-text);
          padding: 8px 10px;
          border-radius: 8px;
          font-size: 0.82rem;
          line-height: 1.2rem;
          opacity: 0;
          pointer-events: none;
          transform: translateY(6px);
          transition: opacity 0.15s ease, transform 0.15s ease;
          z-index: 10;
        }}
        .sf-citation:hover::after {{
          opacity: 1;
          transform: translateY(0);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
