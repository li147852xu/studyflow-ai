from __future__ import annotations

import streamlit as st


def app_shell() -> tuple[st.delta_generator.DeltaGenerator, ...]:
    return st.columns([1.1, 2.4, 1.1], gap="large")
