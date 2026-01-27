from __future__ import annotations

import streamlit as st

from app.help_content import get_help_sections
from app.ui.i18n import t


def render_help(*, workspace_id: str | None = None) -> None:
    language = st.session_state.get("ui_language", "en")
    sections = get_help_sections(language)
    st.caption(t("help_caption", workspace_id))
    for section in sections:
        with st.expander(section["title"], expanded=section.get("expanded", False)):
            for paragraph in section.get("paragraphs", []):
                st.write(paragraph)
            for bullet in section.get("bullets", []):
                st.write(f"- {bullet}")
            code = section.get("code")
            if code:
                st.code(code, language="bash")
