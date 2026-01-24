from __future__ import annotations

import streamlit as st


def three_column_layout() -> tuple[st.delta_generator.DeltaGenerator, ...]:
    return st.columns([1.1, 2.2, 1.1], gap="large")
