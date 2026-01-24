from __future__ import annotations

import streamlit as st


def app_shell() -> tuple[st.delta_generator.DeltaGenerator, ...]:
    st.set_page_config(layout="wide", page_title="StudyFlow-AI")
    return st.columns([1.1, 2.4, 1.1], gap="large")
