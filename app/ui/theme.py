from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    theme = st.session_state.get("ui_theme", "light")

    if theme == "dark":
        bg_color = "#0E1117"
        secondary_bg = "#1A1D24"
        text_color = "#F1F5F9"
        card_border = "#2D3748"
        card_bg = "#1E2530"
        muted_text = "#94A3B8"
        surface_bg = "#151922"
        citation_bg = "#0B1220"
        citation_text = "#E2E8F0"
        shadow_sm = "0 1px 2px rgba(0, 0, 0, 0.3)"
        shadow_md = "0 4px 12px rgba(0, 0, 0, 0.4)"
        shadow_lg = "0 8px 24px rgba(0, 0, 0, 0.5)"
        primary_color = "#3B82F6"
        primary_hover = "#2563EB"
        primary_light = "rgba(59, 130, 246, 0.15)"
        success_color = "#10B981"
        success_light = "rgba(16, 185, 129, 0.15)"
        warning_color = "#F59E0B"
        warning_light = "rgba(245, 158, 11, 0.15)"
        error_color = "#EF4444"
        error_light = "rgba(239, 68, 68, 0.15)"
        content_bg = "#1A1F2E"
        content_text = "#E2E8F0"
        divider_color = "#2D3748"
        input_bg = "#1E2530"
        focus_ring = "rgba(59, 130, 246, 0.4)"
    else:
        bg_color = "#FFFFFF"
        secondary_bg = "#F8FAFC"
        text_color = "#1E293B"
        card_border = "#E2E8F0"
        card_bg = "#FFFFFF"
        muted_text = "#64748B"
        surface_bg = "#F1F5F9"
        citation_bg = "#0F172A"
        citation_text = "#F8FAFC"
        shadow_sm = "0 1px 2px rgba(15, 23, 42, 0.06)"
        shadow_md = "0 4px 12px rgba(15, 23, 42, 0.08)"
        shadow_lg = "0 8px 24px rgba(15, 23, 42, 0.12)"
        primary_color = "#3B82F6"
        primary_hover = "#2563EB"
        primary_light = "rgba(59, 130, 246, 0.08)"
        success_color = "#10B981"
        success_light = "rgba(16, 185, 129, 0.1)"
        warning_color = "#F59E0B"
        warning_light = "rgba(245, 158, 11, 0.1)"
        error_color = "#EF4444"
        error_light = "rgba(239, 68, 68, 0.1)"
        content_bg = "#FFFFFF"
        content_text = "#1E293B"
        divider_color = "#E2E8F0"
        input_bg = "#FFFFFF"
        focus_ring = "rgba(59, 130, 246, 0.25)"

    st.markdown(
        f"""
        <style>
        :root {{
          /* Core colors */
          --bg-color: {bg_color};
          --secondary-bg: {secondary_bg};
          --text-color: {text_color};
          --muted-text: {muted_text};
          --divider-color: {divider_color};

          /* Card & surface */
          --card-bg: {card_bg};
          --card-border: {card_border};
          --surface-bg: {surface_bg};
          --input-bg: {input_bg};

          /* Primary brand */
          --primary-color: {primary_color};
          --primary-hover: {primary_hover};
          --primary-light: {primary_light};

          /* Semantic colors */
          --success-color: {success_color};
          --success-light: {success_light};
          --warning-color: {warning_color};
          --warning-light: {warning_light};
          --error-color: {error_color};
          --error-light: {error_light};

          /* Shadows */
          --shadow-sm: {shadow_sm};
          --shadow-md: {shadow_md};
          --shadow-lg: {shadow_lg};

          /* Focus */
          --focus-ring: {focus_ring};

          /* Content display */
          --content-bg: {content_bg};
          --content-text: {content_text};
          --citation-bg: {citation_bg};
          --citation-text: {citation_text};

          /* Spacing */
          --space-xs: 4px;
          --space-sm: 8px;
          --space-md: 16px;
          --space-lg: 24px;
          --space-xl: 32px;
          --space-2xl: 48px;

          /* Border radius */
          --radius-sm: 6px;
          --radius-md: 10px;
          --radius-lg: 14px;
          --radius-xl: 20px;
          --radius-full: 9999px;

          /* Transitions */
          --transition-fast: 0.1s ease;
          --transition-normal: 0.2s ease;
          --transition-slow: 0.3s ease;
        }}

        /* Base typography */
        html, body, [class*="st-"] {{
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }}

        /* Main app background */
        .stApp {{
          background-color: var(--bg-color);
        }}

        .main .block-container {{
          background-color: var(--bg-color);
          padding-top: 1.5rem;
          padding-bottom: 2rem;
          max-width: 1400px;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
          background-color: var(--secondary-bg);
          border-right: 1px solid var(--card-border);
        }}

        section[data-testid="stSidebar"] > div:first-child {{
          padding-top: 1.5rem;
        }}

        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {{
          display: none;
        }}

        /* Text colors */
        .stMarkdown, .stMarkdown p, .stMarkdown span {{
          color: var(--text-color) !important;
          line-height: 1.6;
        }}

        h1, h2, h3, h4, h5, h6 {{
          color: var(--text-color) !important;
          font-weight: 600;
          letter-spacing: -0.02em;
        }}

        h1 {{ font-size: 2rem; margin-bottom: var(--space-md); }}
        h2 {{ font-size: 1.5rem; margin-bottom: var(--space-sm); }}
        h3 {{ font-size: 1.25rem; margin-bottom: var(--space-sm); }}
        h4 {{ font-size: 1.1rem; margin-bottom: var(--space-xs); }}

        /* ===============================
           FORM CONTROLS
           =============================== */

        /* Input fields */
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input,
        .stTimeInput input {{
          background-color: var(--input-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          color: var(--text-color) !important;
          border-radius: var(--radius-md) !important;
          padding: 10px 14px !important;
          font-size: 14px !important;
          transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
        }}

        .stTextInput input:hover,
        .stTextArea textarea:hover {{
          border-color: var(--muted-text) !important;
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {{
          border-color: var(--primary-color) !important;
          box-shadow: 0 0 0 3px var(--focus-ring) !important;
          outline: none !important;
        }}

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
          color: var(--muted-text) !important;
          opacity: 0.7;
        }}

        /* Input labels */
        .stTextInput label,
        .stTextArea label,
        .stNumberInput label,
        .stSelectbox label,
        .stDateInput label {{
          color: var(--text-color) !important;
          font-weight: 500 !important;
          font-size: 14px !important;
          margin-bottom: var(--space-xs) !important;
        }}

        /* Selectbox */
        .stSelectbox div[data-baseweb="select"] > div {{
          background-color: var(--input-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
          min-height: 44px;
          transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
        }}

        .stSelectbox div[data-baseweb="select"] > div:hover {{
          border-color: var(--muted-text) !important;
        }}

        .stSelectbox div[data-baseweb="select"] > div:focus-within {{
          border-color: var(--primary-color) !important;
          box-shadow: 0 0 0 3px var(--focus-ring) !important;
        }}

        .stSelectbox div[data-baseweb="select"] > div > div {{
          color: var(--text-color) !important;
        }}

        .stSelectbox svg {{
          fill: var(--muted-text) !important;
        }}

        /* Multiselect */
        .stMultiSelect div[data-baseweb="select"] > div {{
          background-color: var(--input-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
        }}

        /* Checkbox */
        .stCheckbox label {{
          color: var(--text-color) !important;
        }}

        .stCheckbox label span[data-testid="stMarkdownContainer"] {{
          color: var(--text-color) !important;
        }}

        /* ===============================
           BUTTONS
           =============================== */

        .stButton > button {{
          border-radius: var(--radius-md) !important;
          font-weight: 500 !important;
          font-size: 14px !important;
          padding: 10px 20px !important;
          transition: all var(--transition-fast) !important;
          border: 1.5px solid var(--card-border) !important;
          background-color: var(--card-bg) !important;
          color: var(--text-color) !important;
          box-shadow: var(--shadow-sm) !important;
          min-height: 42px !important;
        }}

        .stButton > button:hover {{
          background-color: var(--surface-bg) !important;
          border-color: var(--primary-color) !important;
          box-shadow: var(--shadow-md) !important;
          transform: translateY(-1px);
        }}

        .stButton > button:active {{
          transform: translateY(0);
          box-shadow: var(--shadow-sm) !important;
        }}

        .stButton > button:disabled {{
          opacity: 0.5 !important;
          cursor: not-allowed !important;
          transform: none !important;
        }}

        /* Primary button */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {{
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%) !important;
          color: white !important;
          border-color: var(--primary-color) !important;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
        }}

        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {{
          background: linear-gradient(135deg, var(--primary-hover) 0%, #1D4ED8 100%) !important;
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        }}

        /* Secondary button */
        .stButton > button[kind="secondary"],
        .stButton > button[data-testid="baseButton-secondary"] {{
          background-color: var(--primary-light) !important;
          color: var(--primary-color) !important;
          border-color: var(--primary-color) !important;
        }}

        /* Download button */
        .stDownloadButton > button {{
          border-radius: var(--radius-md) !important;
          font-weight: 500 !important;
          transition: all var(--transition-fast) !important;
        }}

        /* ===============================
           EXPANDERS
           =============================== */

        .streamlit-expanderHeader {{
          background-color: var(--surface-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
          font-weight: 500 !important;
          color: var(--text-color) !important;
          padding: 12px 16px !important;
          transition: all var(--transition-fast) !important;
        }}

        .streamlit-expanderHeader:hover {{
          background-color: var(--primary-light) !important;
          border-color: var(--primary-color) !important;
        }}

        .streamlit-expanderContent {{
          background-color: var(--card-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          border-top: none !important;
          border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
          padding: var(--space-md) !important;
        }}

        /* Expander icon */
        .streamlit-expanderHeader svg {{
          fill: var(--muted-text) !important;
          transition: transform var(--transition-fast) !important;
        }}

        /* ===============================
           TABS
           =============================== */

        .stTabs [data-baseweb="tab-list"] {{
          background-color: var(--surface-bg);
          border-radius: var(--radius-lg);
          padding: 6px;
          gap: 6px;
          border: 1px solid var(--card-border);
        }}

        .stTabs [data-baseweb="tab"] {{
          border-radius: var(--radius-md) !important;
          padding: 10px 20px !important;
          font-weight: 500 !important;
          font-size: 14px !important;
          color: var(--muted-text) !important;
          transition: all var(--transition-fast) !important;
          border: none !important;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
          color: var(--text-color) !important;
          background-color: var(--card-bg) !important;
        }}

        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
          background-color: var(--card-bg) !important;
          color: var(--primary-color) !important;
          box-shadow: var(--shadow-md);
        }}

        .stTabs [data-baseweb="tab-highlight"] {{
          display: none !important;
        }}

        /* Tab panel content */
        .stTabs [data-baseweb="tab-panel"] {{
          padding-top: var(--space-lg) !important;
        }}

        /* ===============================
           METRICS
           =============================== */

        [data-testid="stMetric"] {{
          background-color: var(--surface-bg);
          border-radius: var(--radius-md);
          padding: var(--space-md);
          border: 1px solid var(--card-border);
        }}

        [data-testid="stMetricValue"] {{
          color: var(--text-color) !important;
          font-weight: 700 !important;
          font-size: 1.5rem !important;
        }}

        [data-testid="stMetricLabel"] {{
          color: var(--muted-text) !important;
          font-size: 0.875rem !important;
          font-weight: 500 !important;
        }}

        [data-testid="stMetricDelta"] {{
          font-size: 0.875rem !important;
        }}

        /* ===============================
           MISC ELEMENTS
           =============================== */

        /* JSON display */
        .stJson {{
          background-color: var(--surface-bg) !important;
          border: 1px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
        }}

        /* Caption */
        .stCaption, [data-testid="stCaption"] {{
          color: var(--muted-text) !important;
          font-size: 0.875rem !important;
        }}

        /* Divider */
        .stDivider {{
          border-color: var(--divider-color) !important;
        }}

        hr {{
          border-color: var(--divider-color) !important;
          opacity: 0.5;
        }}

        /* Progress bar */
        .stProgress > div > div {{
          background-color: var(--primary-color) !important;
          border-radius: var(--radius-full) !important;
        }}

        .stProgress > div {{
          background-color: var(--surface-bg) !important;
          border-radius: var(--radius-full) !important;
        }}

        /* Spinner */
        .stSpinner > div {{
          border-top-color: var(--primary-color) !important;
        }}

        /* ===============================
           CUSTOM COMPONENTS
           =============================== */

        /* Section title */
        .sf-section-title {{
          font-size: 1.75rem !important;
          font-weight: 700 !important;
          color: var(--text-color) !important;
          margin: 0 0 var(--space-lg) 0 !important;
          letter-spacing: -0.02em;
        }}

        .sf-muted {{
          color: var(--muted-text) !important;
        }}

        /* Content display box - for generated results */
        .sf-content-box {{
          background-color: var(--content-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          border-radius: var(--radius-lg) !important;
          padding: var(--space-lg) var(--space-xl) !important;
          margin: var(--space-md) 0 !important;
          color: var(--content-text) !important;
          line-height: 1.7 !important;
          box-shadow: var(--shadow-sm);
        }}

        .sf-content-box p,
        .sf-content-box li,
        .sf-content-box span {{
          color: var(--content-text) !important;
        }}

        .sf-content-box h1,
        .sf-content-box h2,
        .sf-content-box h3,
        .sf-content-box h4,
        .sf-content-box h5 {{
          color: var(--content-text) !important;
          margin-top: var(--space-lg);
          margin-bottom: var(--space-sm);
          font-weight: 600;
        }}

        .sf-content-box h1 {{ font-size: 1.5rem; }}
        .sf-content-box h2 {{ font-size: 1.3rem; }}
        .sf-content-box h3 {{ font-size: 1.15rem; }}

        .sf-content-box code {{
          background-color: var(--surface-bg);
          padding: 2px 8px;
          border-radius: var(--radius-sm);
          font-size: 0.9em;
          font-family: 'SF Mono', Monaco, Consolas, monospace;
        }}

        .sf-content-box ul, .sf-content-box ol {{
          padding-left: 24px;
          margin: var(--space-sm) 0;
        }}

        .sf-content-box li {{
          margin-bottom: var(--space-xs);
        }}

        .sf-content-box strong {{
          font-weight: 600;
          color: var(--text-color) !important;
        }}

        /* ===============================
           CARD STYLES
           =============================== */

        .sf-card {{
          background: var(--card-bg) !important;
          border: 1.5px solid var(--card-border) !important;
          border-radius: var(--radius-lg) !important;
          padding: var(--space-lg) !important;
          margin-bottom: var(--space-md) !important;
          box-shadow: var(--shadow-sm) !important;
          transition: all var(--transition-normal) !important;
        }}

        .sf-card:hover {{
          box-shadow: var(--shadow-md) !important;
          border-color: var(--primary-color) !important;
        }}

        /* Document card for library */
        .sf-doc-card {{
          background: var(--card-bg);
          border: 1.5px solid var(--card-border);
          border-radius: var(--radius-md);
          padding: var(--space-md) var(--space-lg);
          margin-bottom: var(--space-sm);
          display: flex;
          align-items: center;
          gap: var(--space-md);
          transition: all var(--transition-fast);
          cursor: pointer;
        }}

        .sf-doc-card:hover {{
          border-color: var(--primary-color);
          background: var(--primary-light);
          transform: translateX(4px);
        }}

        .sf-doc-icon {{
          font-size: 1.75rem;
          line-height: 1;
        }}

        .sf-doc-info {{
          flex: 1;
          min-width: 0;
        }}

        .sf-doc-name {{
          font-weight: 600;
          color: var(--text-color);
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }}

        .sf-doc-meta {{
          font-size: 0.8rem;
          color: var(--muted-text);
        }}

        .sf-doc-type {{
          padding: 4px 10px;
          border-radius: var(--radius-full);
          font-size: 0.75rem;
          font-weight: 600;
          background: var(--surface-bg);
          color: var(--muted-text);
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }}

        /* ===============================
           CHIPS & TAGS
           =============================== */

        .sf-chip {{
          display: inline-flex;
          align-items: center;
          padding: 5px 12px;
          border-radius: var(--radius-full);
          font-size: 0.8rem;
          font-weight: 500;
          background: var(--surface-bg);
          color: var(--muted-text);
          border: 1px solid var(--card-border);
          margin-right: var(--space-xs);
          margin-bottom: var(--space-xs);
          transition: all var(--transition-fast);
        }}

        .sf-chip:hover {{
          background: var(--primary-light);
          color: var(--primary-color);
          border-color: var(--primary-color);
        }}

        .sf-chip-primary {{
          background: var(--primary-light);
          color: var(--primary-color);
          border-color: transparent;
        }}

        .sf-chip-success {{
          background: var(--success-light);
          color: var(--success-color);
          border-color: transparent;
        }}

        .sf-chip-warning {{
          background: var(--warning-light);
          color: var(--warning-color);
          border-color: transparent;
        }}

        .sf-chip-error {{
          background: var(--error-light);
          color: var(--error-color);
          border-color: transparent;
        }}

        /* ===============================
           STATUS INDICATORS
           =============================== */

        .sf-status-success {{
          color: var(--success-color) !important;
        }}

        .sf-status-warning {{
          color: var(--warning-color) !important;
        }}

        .sf-status-error {{
          color: var(--error-color) !important;
        }}

        .sf-status-badge {{
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: var(--radius-full);
          font-size: 0.8rem;
          font-weight: 600;
        }}

        .sf-status-badge-success {{
          background: var(--success-light);
          color: var(--success-color);
        }}

        .sf-status-badge-warning {{
          background: var(--warning-light);
          color: var(--warning-color);
        }}

        .sf-status-badge-error {{
          background: var(--error-light);
          color: var(--error-color);
        }}

        .sf-status-badge-info {{
          background: var(--primary-light);
          color: var(--primary-color);
        }}

        /* ===============================
           CITATIONS
           =============================== */

        .sf-citation {{
          position: relative;
          cursor: help;
          color: var(--primary-color);
          font-weight: 600;
          text-decoration: underline;
          text-decoration-style: dotted;
          text-underline-offset: 2px;
        }}

        .sf-citation::after {{
          content: attr(data-tooltip);
          position: absolute;
          left: 0;
          bottom: 125%;
          min-width: 300px;
          max-width: 420px;
          background: var(--citation-bg);
          color: var(--citation-text);
          padding: 12px 16px;
          border-radius: var(--radius-md);
          font-size: 0.85rem;
          line-height: 1.5;
          opacity: 0;
          pointer-events: none;
          transform: translateY(8px);
          transition: opacity var(--transition-fast), transform var(--transition-fast);
          z-index: 1000;
          box-shadow: var(--shadow-lg);
          font-weight: 400;
          text-decoration: none;
        }}

        .sf-citation:hover::after {{
          opacity: 1;
          transform: translateY(0);
        }}

        /* ===============================
           EMPTY STATE
           =============================== */

        .sf-empty-state {{
          text-align: center;
          padding: var(--space-2xl) var(--space-xl);
          color: var(--muted-text);
          background: var(--surface-bg);
          border-radius: var(--radius-xl);
          border: 2px dashed var(--card-border);
          margin: var(--space-lg) 0;
        }}

        .sf-empty-icon {{
          font-size: 4rem;
          margin-bottom: var(--space-md);
          opacity: 0.4;
          line-height: 1;
        }}

        .sf-empty-title {{
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--text-color);
          margin-bottom: var(--space-sm);
        }}

        .sf-empty-desc {{
          font-size: 0.95rem;
          color: var(--muted-text);
          max-width: 400px;
          margin: 0 auto;
          line-height: 1.5;
        }}

        /* ===============================
           HEADER CARD
           =============================== */

        .sf-header-card {{
          background: linear-gradient(135deg, var(--primary-light) 0%, transparent 100%);
          border: 1.5px solid rgba(59, 130, 246, 0.2);
          border-radius: var(--radius-lg);
          padding: var(--space-lg) var(--space-xl);
          margin-bottom: var(--space-lg);
          position: relative;
          overflow: hidden;
        }}

        .sf-header-card::before {{
          content: '';
          position: absolute;
          top: 0;
          right: 0;
          width: 200px;
          height: 200px;
          background: radial-gradient(circle, var(--primary-light) 0%, transparent 70%);
          opacity: 0.5;
        }}

        .sf-header-title {{
          font-size: 1.4rem;
          font-weight: 700;
          color: var(--text-color);
          margin-bottom: var(--space-xs);
          position: relative;
        }}

        .sf-header-subtitle {{
          font-size: 0.95rem;
          color: var(--muted-text);
          position: relative;
        }}

        /* ===============================
           NOTIFICATION CENTER
           =============================== */

        .sf-notification {{
          background: var(--card-bg);
          border: 1.5px solid var(--card-border);
          border-left: 4px solid var(--primary-color);
          border-radius: var(--radius-md);
          padding: var(--space-md) var(--space-lg);
          margin-bottom: var(--space-sm);
          transition: all var(--transition-fast);
        }}

        .sf-notification:hover {{
          background: var(--surface-bg);
        }}

        .sf-notification-success {{
          border-left-color: var(--success-color);
          background: var(--success-light);
        }}

        .sf-notification-warning {{
          border-left-color: var(--warning-color);
          background: var(--warning-light);
        }}

        .sf-notification-error {{
          border-left-color: var(--error-color);
          background: var(--error-light);
        }}

        /* ===============================
           LAYOUT HELPERS
           =============================== */

        .sf-divider {{
          border-top: 1px solid var(--divider-color);
          margin: var(--space-lg) 0;
        }}

        .sf-grid {{
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: var(--space-md);
        }}

        .sf-grid-2 {{
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-md);
        }}

        .sf-grid-3 {{
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-md);
        }}

        .sf-flex {{
          display: flex;
          align-items: center;
          gap: var(--space-md);
        }}

        .sf-flex-between {{
          display: flex;
          align-items: center;
          justify-content: space-between;
        }}

        /* ===============================
           ALERTS & FEEDBACK
           =============================== */

        .stAlert {{
          border-radius: var(--radius-md) !important;
          padding: var(--space-md) var(--space-lg) !important;
        }}

        div[data-testid="stAlert"] {{
          border-radius: var(--radius-md) !important;
        }}

        /* Success alert */
        div[data-testid="stAlert"][data-baseweb*="positive"],
        .stSuccess {{
          background-color: var(--success-light) !important;
          border-color: var(--success-color) !important;
          border-left: 4px solid var(--success-color) !important;
        }}

        /* Warning alert */
        div[data-testid="stAlert"][data-baseweb*="warning"],
        .stWarning {{
          background-color: var(--warning-light) !important;
          border-color: var(--warning-color) !important;
          border-left: 4px solid var(--warning-color) !important;
        }}

        /* Error alert */
        div[data-testid="stAlert"][data-baseweb*="negative"],
        .stError {{
          background-color: var(--error-light) !important;
          border-color: var(--error-color) !important;
          border-left: 4px solid var(--error-color) !important;
        }}

        /* Info alert */
        div[data-testid="stAlert"][data-baseweb*="info"],
        .stInfo {{
          background-color: var(--primary-light) !important;
          border-color: var(--primary-color) !important;
          border-left: 4px solid var(--primary-color) !important;
        }}

        /* ===============================
           FORM STATES
           =============================== */

        /* Disabled text areas */
        .stTextArea textarea:disabled {{
          color: var(--text-color) !important;
          opacity: 0.85 !important;
          -webkit-text-fill-color: var(--text-color) !important;
          background-color: var(--surface-bg) !important;
        }}

        /* Disabled buttons */
        .stButton > button:disabled {{
          opacity: 0.5 !important;
          cursor: not-allowed !important;
          background-color: var(--surface-bg) !important;
        }}

        /* ===============================
           HELP TOOLTIPS
           =============================== */

        [data-testid="stTooltipHoverTarget"] {{
          color: var(--muted-text) !important;
        }}

        [data-testid="stTooltipHoverTarget"] svg {{
          fill: var(--muted-text) !important;
          opacity: 0.6;
          transition: all var(--transition-fast);
        }}

        [data-testid="stTooltipHoverTarget"]:hover svg {{
          opacity: 1;
          fill: var(--primary-color) !important;
        }}

        section[data-testid="stSidebar"] [data-testid="stTooltipHoverTarget"] svg {{
          fill: var(--muted-text) !important;
        }}

        /* ===============================
           DATAFRAME / TABLE
           =============================== */

        .stDataFrame {{
          border-radius: var(--radius-md) !important;
          overflow: hidden;
        }}

        .stDataFrame [data-testid="stDataFrameResizable"] {{
          border: 1px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
        }}

        /* ===============================
           TOAST NOTIFICATIONS
           =============================== */

        [data-testid="stToast"] {{
          border-radius: var(--radius-md) !important;
          box-shadow: var(--shadow-lg) !important;
        }}

        /* ===============================
           TOP TOOLBAR / HEADER BAR
           =============================== */

        header[data-testid="stHeader"] {{
          background-color: var(--bg-color) !important;
          backdrop-filter: blur(10px);
          border-bottom: 1px solid var(--divider-color);
        }}

        header[data-testid="stHeader"] button {{
          color: var(--muted-text) !important;
        }}

        header[data-testid="stHeader"] button:hover {{
          color: var(--text-color) !important;
        }}

        /* App viewer menu */
        [data-testid="stAppViewContainer"] > section > div > div > header {{
          background-color: var(--bg-color) !important;
        }}

        /* Toolbar buttons */
        [data-testid="stToolbar"] {{
          background-color: transparent !important;
        }}

        [data-testid="stToolbar"] button {{
          color: var(--muted-text) !important;
          background-color: transparent !important;
        }}

        [data-testid="stToolbar"] button:hover {{
          color: var(--primary-color) !important;
          background-color: var(--primary-light) !important;
        }}

        /* Decoration container (top bar area) */
        [data-testid="stDecoration"] {{
          background-color: var(--bg-color) !important;
        }}

        /* ===============================
           MODERN EXPANDER SELECTORS
           =============================== */

        [data-testid="stExpander"] {{
          border: 1.5px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
          overflow: hidden;
          margin-bottom: var(--space-md);
        }}

        [data-testid="stExpander"] > div:first-child {{
          background-color: var(--surface-bg) !important;
          border: none !important;
          padding: 12px 16px !important;
          transition: all var(--transition-fast) !important;
        }}

        [data-testid="stExpander"] > div:first-child:hover {{
          background-color: var(--primary-light) !important;
        }}

        [data-testid="stExpander"] > div:first-child p {{
          color: var(--text-color) !important;
          font-weight: 500 !important;
        }}

        [data-testid="stExpander"] > div:first-child svg {{
          fill: var(--muted-text) !important;
        }}

        [data-testid="stExpander"] > div:last-child {{
          background-color: var(--card-bg) !important;
          border-top: 1px solid var(--divider-color) !important;
          padding: var(--space-md) !important;
        }}

        /* ===============================
           POPOVER / DROPDOWN MENUS
           =============================== */

        [data-baseweb="popover"] {{
          background-color: var(--card-bg) !important;
          border: 1px solid var(--card-border) !important;
          border-radius: var(--radius-md) !important;
          box-shadow: var(--shadow-lg) !important;
        }}

        [data-baseweb="popover"] li {{
          color: var(--text-color) !important;
        }}

        [data-baseweb="popover"] li:hover {{
          background-color: var(--primary-light) !important;
        }}

        [data-baseweb="menu"] {{
          background-color: var(--card-bg) !important;
          border: 1px solid var(--card-border) !important;
        }}

        [data-baseweb="menu"] li {{
          color: var(--text-color) !important;
        }}

        [data-baseweb="menu"] li:hover {{
          background-color: var(--surface-bg) !important;
        }}

        /* ===============================
           NOTIFICATION CENTER STYLING
           =============================== */

        .sf-notification-card {{
          background: var(--card-bg);
          border: 1px solid var(--card-border);
          border-radius: var(--radius-md);
          padding: 12px 16px;
          margin-bottom: 10px;
        }}

        .sf-notification-running {{
          background: var(--warning-light);
          border: 1px solid var(--warning-color);
          border-radius: var(--radius-md);
          padding: 12px 16px;
          margin-bottom: 12px;
        }}

        .sf-notification-title {{
          color: var(--text-color);
          font-weight: 600;
        }}

        .sf-notification-status-running {{
          color: var(--warning-color);
        }}

        .sf-notification-status-success {{
          color: var(--success-color);
        }}

        .sf-notification-status-error {{
          color: var(--error-color);
        }}

        .sf-notification-summary {{
          color: var(--muted-text);
          font-size: 0.85rem;
        }}

        /* ===============================
           INFO / SUCCESS / WARNING / ERROR BOXES
           =============================== */

        [data-testid="stAlert"] {{
          border-radius: var(--radius-md) !important;
        }}

        .stAlert {{
          border-radius: var(--radius-md) !important;
        }}

        div[data-baseweb="notification"] {{
          border-radius: var(--radius-md) !important;
        }}

        /* ===============================
           ANIMATIONS
           =============================== */

        @keyframes sf-fade-in {{
          from {{ opacity: 0; transform: translateY(10px); }}
          to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes sf-pulse {{
          0%, 100% {{ opacity: 1; }}
          50% {{ opacity: 0.5; }}
        }}

        .sf-animate-in {{
          animation: sf-fade-in 0.3s ease forwards;
        }}

        .sf-pulse {{
          animation: sf-pulse 1.5s ease-in-out infinite;
        }}

        /* ===============================
           COURSE CARD
           =============================== */

        .sf-course-card {{
          background: var(--card-bg);
          border: 1.5px solid var(--card-border);
          border-radius: var(--radius-lg);
          padding: var(--space-lg);
          transition: all var(--transition-normal);
          cursor: pointer;
        }}

        .sf-course-card:hover {{
          border-color: var(--primary-color);
          box-shadow: var(--shadow-md);
          transform: translateY(-2px);
        }}

        .sf-course-card-title {{
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--text-color);
          margin-bottom: var(--space-xs);
        }}

        .sf-course-card-meta {{
          font-size: 0.85rem;
          color: var(--muted-text);
        }}

        .sf-course-card-badge {{
          display: inline-block;
          padding: 2px 8px;
          border-radius: var(--radius-full);
          font-size: 0.75rem;
          font-weight: 600;
          background: var(--primary-light);
          color: var(--primary-color);
          margin-top: var(--space-sm);
        }}

        /* ===============================
           STAT CARD
           =============================== */

        .sf-stat-card {{
          background: var(--card-bg);
          border: 1.5px solid var(--card-border);
          border-radius: var(--radius-lg);
          padding: var(--space-lg);
          text-align: center;
        }}

        .sf-stat-value {{
          font-size: 2rem;
          font-weight: 700;
          color: var(--primary-color);
          line-height: 1;
        }}

        .sf-stat-label {{
          font-size: 0.9rem;
          color: var(--muted-text);
          margin-top: var(--space-xs);
        }}

        /* ===============================
           LIST ITEM
           =============================== */

        .sf-list-item {{
          display: flex;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-md);
          border-radius: var(--radius-md);
          transition: background var(--transition-fast);
        }}

        .sf-list-item:hover {{
          background: var(--surface-bg);
        }}

        .sf-list-item-icon {{
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--primary-light);
          border-radius: var(--radius-md);
          font-size: 1.25rem;
        }}

        .sf-list-item-content {{
          flex: 1;
          min-width: 0;
        }}

        .sf-list-item-title {{
          font-weight: 500;
          color: var(--text-color);
        }}

        .sf-list-item-desc {{
          font-size: 0.85rem;
          color: var(--muted-text);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
