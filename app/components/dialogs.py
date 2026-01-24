from __future__ import annotations

import streamlit as st


def confirm_action(*, key: str, label: str, help_text: str | None = None) -> bool:
    return st.checkbox(label, key=key, help=help_text)
