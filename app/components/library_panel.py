from __future__ import annotations

import streamlit as st

from app.components.chat_panel import render_chat_panel
from app.components.library_view import render_library_view


def render_library_panel(
    *,
    left: st.delta_generator.DeltaGenerator,
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str,
    api_adapter,
    retrieval_mode: str,
    api_mode: str,
) -> None:
    render_library_view(
        left=left,
        center=center,
        right=right,
        workspace_id=workspace_id,
        api_adapter=api_adapter,
    )
    with center:
        render_chat_panel(
            workspace_id=workspace_id,
            default_retrieval_mode=retrieval_mode,
            api_adapter=api_adapter,
            api_mode=api_mode,
        )
