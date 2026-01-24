from __future__ import annotations

import streamlit as st

from app.components.help_view import render_help


def render_help_center() -> None:
    st.markdown("### Help Center")
    render_help()
