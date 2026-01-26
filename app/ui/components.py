from __future__ import annotations

import streamlit as st

from app.ui.i18n import t


def section_title(text: str) -> None:
    st.markdown(f"<div class='sf-section-title'>{text}</div>", unsafe_allow_html=True)


def muted(text: str) -> None:
    st.markdown(f"<span class='sf-muted'>{text}</span>", unsafe_allow_html=True)


def card_header(title: str, subtitle: str | None = None) -> None:
    st.markdown("<div class='sf-card'>", unsafe_allow_html=True)
    section_title(title)
    if subtitle:
        muted(subtitle)


def card_footer() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_inspector(
    *,
    status: dict | None = None,
    citations: list[str] | None = None,
    exports: list[dict] | None = None,
    history: list[dict] | None = None,
    versions: list[dict] | None = None,
) -> None:
    st.markdown(f"### {t('inspector')}")
    collapsed = st.checkbox(
        t("collapse_inspector"),
        value=st.session_state.get("inspector_collapsed", False),
    )
    st.session_state["inspector_collapsed"] = collapsed
    if collapsed:
        st.caption(t("inspector_collapsed"))
        return

    if status:
        with st.expander(t("status"), expanded=True):
            for key, value in status.items():
                st.write(f"{key}: {value}")

    if citations:
        with st.expander(t("citations"), expanded=False):
            for citation in citations:
                st.write(citation)

    if exports:
        with st.expander(t("exports"), expanded=False):
            for item in exports:
                st.write(item)

    if versions:
        with st.expander(t("versions"), expanded=False):
            for item in versions:
                st.write(item)

    if history:
        with st.expander(t("history"), expanded=False):
            for item in history:
                st.write(item)


def run_with_progress(
    *,
    label: str,
    work: callable,
    success_label: str | None = None,
    error_label: str | None = None,
) -> tuple[bool, object | None]:
    status = st.status(label, expanded=False)
    progress = st.progress(0.05)
    try:
        result = work()
        progress.progress(1.0)
        status.update(
            label=success_label or label,
            state="complete",
        )
        return True, result
    except Exception as exc:
        progress.progress(1.0)
        status.update(
            label=error_label or label,
            state="error",
        )
        st.error(str(exc))
        return False, None
