from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --card-border: #E2E8F0;
          --card-bg: #FFFFFF;
          --muted-text: #64748B;
        }
        .sf-card {
          border: 1px solid var(--card-border);
          background: var(--card-bg);
          border-radius: 12px;
          padding: 16px;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
          margin-bottom: 16px;
        }
        .sf-muted {
          color: var(--muted-text);
        }
        .sf-section-title {
          font-size: 1.05rem;
          font-weight: 600;
          margin-bottom: 6px;
        }
        .sf-chip {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 999px;
          border: 1px solid var(--card-border);
          background: #F8FAFC;
          margin-right: 6px;
          font-size: 0.8rem;
        }
        .sf-divider {
          border-top: 1px solid var(--card-border);
          margin: 12px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
