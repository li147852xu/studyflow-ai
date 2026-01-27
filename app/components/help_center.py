from __future__ import annotations

import streamlit as st

from app.components.help_view import render_help
from app.ui.i18n import t


def render_help_center(*, workspace_id: str | None = None) -> None:
    st.markdown(f"### {t('help_title', workspace_id)}")
    render_help(workspace_id=workspace_id)
