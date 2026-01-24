from __future__ import annotations

import streamlit as st

from app.help_content import HELP_SECTIONS


def render_help() -> None:
    st.markdown("### Help / Docs")
    st.caption("Use the sections below to learn the workflow and troubleshoot issues.")
    for section in HELP_SECTIONS:
        with st.expander(section["title"], expanded=section.get("expanded", False)):
            for paragraph in section.get("paragraphs", []):
                st.write(paragraph)
            for bullet in section.get("bullets", []):
                st.write(f"- {bullet}")
            code = section.get("code")
            if code:
                st.code(code, language="bash")
