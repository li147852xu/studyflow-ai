from __future__ import annotations

import streamlit as st

from app.ui.components import render_inspector
from app.ui.i18n import t
from app.help_content import get_help_sections


def render_help_page(
    *,
    main_col: st.delta_generator.DeltaGenerator,
    inspector_col: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
) -> None:
    with main_col:
        st.markdown(f"## {t('help_title', workspace_id)}")
        st.caption(t("help_caption", workspace_id))

        language = st.session_state.get("ui_language", "en")
        sections = get_help_sections(language)

        for section in sections:
            with st.expander(section["title"], expanded=section.get("expanded", False)):
                for paragraph in section.get("paragraphs", []):
                    st.write(paragraph)
                for bullet in section.get("bullets", []):
                    st.write(f"- {bullet}")
                code = section.get("code")
                if code:
                    st.code(code, language="bash")

    with inspector_col:
        render_inspector(
            status={t("project", workspace_id): workspace_id or "-"},
            citations=None,
        )
