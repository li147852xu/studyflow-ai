from __future__ import annotations

import os

import requests
import streamlit as st

from core.ui_state.storage import get_setting, set_setting
from infra.db import get_workspaces_dir


def render_settings_center(
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
) -> None:
    with center:
        st.markdown("### Settings")
        st.caption("Provider settings are stored locally and do not leave your machine.")
        mode = st.radio(
            "UI Mode",
            options=["direct", "api"],
            index=0 if st.session_state.get("api_mode", "direct") == "direct" else 1,
            help="Direct calls local services. API uses FastAPI endpoints.",
        )
        api_base_url = st.text_input(
            "API Base URL",
            value=st.session_state.get("api_base_url", "http://127.0.0.1:8000"),
        )
        base_url = st.text_input(
            "LLM Base URL",
            value=st.session_state.get("llm_base_url", ""),
            key="settings_llm_base_url",
        )
        model = st.text_input(
            "LLM Model",
            value=st.session_state.get("llm_model", ""),
            key="settings_llm_model",
        )
        api_key = st.text_input(
            "LLM API Key",
            value=st.session_state.get("llm_api_key", ""),
            type="password",
            key="settings_llm_api_key",
        )
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.get("llm_temperature", 0.2)),
            step=0.05,
        )
        embed_model = st.text_input(
            "Embedding model (optional)",
            value=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
            key="settings_embed_model",
        )
        st.markdown("#### OCR Settings")
        ocr_mode = st.selectbox(
            "OCR mode",
            options=["off", "auto", "on"],
            index=["off", "auto", "on"].index(
                st.session_state.get("ocr_mode", "off")
            ),
            help="Auto triggers OCR on low-text pages.",
        )
        ocr_threshold = st.slider(
            "OCR threshold (chars)",
            min_value=10,
            max_value=200,
            value=int(st.session_state.get("ocr_threshold", 50)),
            step=10,
        )
        st.markdown("#### Prompt Version")
        prompt_version = st.selectbox(
            "Prompt version",
            options=["v1"],
            index=0,
            help="Select prompt version for generation and coach.",
        )
        if st.button("Save settings"):
            st.session_state["llm_base_url"] = base_url
            st.session_state["llm_model"] = model
            st.session_state["llm_api_key"] = api_key
            st.session_state["llm_temperature"] = temperature
            st.session_state["api_mode"] = mode
            st.session_state["api_base_url"] = api_base_url
            st.session_state["ocr_mode"] = ocr_mode
            st.session_state["ocr_threshold"] = ocr_threshold
            st.session_state["prompt_version"] = prompt_version
            if embed_model:
                os.environ["STUDYFLOW_EMBED_MODEL"] = embed_model
            if base_url:
                set_setting(None, "llm_base_url", base_url)
            if model:
                set_setting(None, "llm_model", model)
            set_setting(None, "llm_temperature", str(temperature))
            set_setting(None, "api_mode", mode)
            set_setting(None, "api_base_url", api_base_url)
            set_setting(None, "ocr_mode", ocr_mode)
            set_setting(None, "ocr_threshold", str(ocr_threshold))
            set_setting(None, "prompt_version", prompt_version)
            st.success("Settings saved.")

        st.markdown("#### Connection tests")
        if st.button("Ping API server"):
            try:
                token = os.getenv("API_TOKEN", "")
                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(
                    f"{api_base_url.rstrip('/')}/health", headers=headers, timeout=10
                )
                if resp.status_code >= 400:
                    st.error(f"API error {resp.status_code}: {resp.text}")
                else:
                    st.success(f"API responded: {resp.json()}")
            except requests.RequestException as exc:
                st.error(f"API ping failed: {exc}")
        if st.button("Test LLM connection"):
            from service.chat_service import chat, ChatConfigError

            try:
                response = chat(
                    prompt="Reply with 'OK' if you can read this.",
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    temperature=0.1,
                )
                st.success(f"LLM responded: {response[:120]}")
            except ChatConfigError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"LLM test failed: {exc}")

        if st.button("Test embedding model"):
            from core.retrieval.embedder import (
                build_embedding_settings,
                embed_texts,
                EmbeddingError,
            )

            try:
                settings = build_embedding_settings()
                embed_texts(["ping"], settings)
                st.success("Embedding model loaded successfully.")
            except EmbeddingError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Embedding test failed: {exc}")

    with right:
        st.markdown("### Storage")
        workspace_dir = get_workspaces_dir()
        st.code(str(workspace_dir))
        if workspace_id:
            st.caption(f"Active workspace: {workspace_id}")
            st.caption(f"Indexes: {workspace_dir}/{workspace_id}/index/")
            st.caption(f"Runs: {workspace_dir}/{workspace_id}/runs/")
            st.caption(f"Outputs: {workspace_dir}/{workspace_id}/outputs/")
        st.caption("Backup tip: copy the workspace folder to another location.")
        st.markdown("### Retrieval mode")
        mode = st.selectbox(
            "Default mode",
            options=["vector", "bm25", "hybrid"],
            index=["vector", "bm25", "hybrid"].index(
                get_setting(workspace_id, "retrieval_mode") if workspace_id else "vector"
            )
            if workspace_id
            else 0,
        )
        if workspace_id and st.button("Save retrieval mode"):
            set_setting(workspace_id, "retrieval_mode", mode)
            st.session_state["retrieval_mode"] = mode
            st.success("Retrieval mode saved.")
