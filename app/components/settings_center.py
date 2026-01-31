from __future__ import annotations

import os

import requests
import streamlit as st

from app.ui.i18n import t
from app.ui.locks import running_task_summary
from core.ui_state.storage import get_setting, set_setting
from infra.db import get_workspaces_dir


def render_settings_center(
    center: st.delta_generator.DeltaGenerator,
    right: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
) -> None:
    locked, lock_msg = running_task_summary(workspace_id)
    with center:
        st.markdown(f"### {t('settings_title', workspace_id)}")
        st.caption(t("settings_caption", workspace_id))
        if lock_msg:
            st.info(lock_msg)
        stored_mode = get_setting(None, "api_mode") or "direct"
        if stored_mode not in {"direct", "api"}:
            stored_mode = "direct"
        st.session_state["api_mode"] = stored_mode
        mode = st.radio(
            t("ui_mode", workspace_id),
            options=["direct", "api"],
            index=0 if stored_mode == "direct" else 1,
            help=t("ui_mode_help", workspace_id),
            format_func=lambda value: t(f"ui_mode_{value}", workspace_id),
        )
        api_base_url = st.text_input(
            t("api_base_url", workspace_id),
            value=st.session_state.get("api_base_url", "http://127.0.0.1:8000"),
            help=t("api_base_url_help", workspace_id),
        )
        base_url = st.text_input(
            t("llm_base_url", workspace_id),
            value=st.session_state.get("llm_base_url", ""),
            key="settings_llm_base_url",
            help=t("llm_base_url_help", workspace_id),
        )
        model = st.text_input(
            t("llm_model", workspace_id),
            value=st.session_state.get("llm_model", ""),
            key="settings_llm_model",
            help=t("llm_model_help", workspace_id),
        )
        api_key = st.text_input(
            t("llm_api_key", workspace_id),
            value=st.session_state.get("llm_api_key", ""),
            type="password",
            key="settings_llm_api_key",
            help=t("llm_api_key_help", workspace_id),
        )
        temperature = st.slider(
            t("temperature", workspace_id),
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.get("llm_temperature", 0.2)),
            step=0.05,
            help=t("temperature_help", workspace_id),
        )
        embed_model = st.text_input(
            t("embedding_model_optional", workspace_id),
            value=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
            key="settings_embed_model",
            help=t("embedding_model_help", workspace_id),
        )
        st.markdown(f"#### {t('ocr_settings', workspace_id)}")
        ocr_mode = st.selectbox(
            t("ocr_mode", workspace_id),
            options=["off", "auto", "on"],
            index=["off", "auto", "on"].index(
                st.session_state.get("ocr_mode", "off")
            ),
            help=t("ocr_mode_help", workspace_id),
            format_func=lambda value: t(f"ocr_mode_{value}", workspace_id),
        )
        ocr_threshold = st.slider(
            t("ocr_threshold", workspace_id),
            min_value=10,
            max_value=200,
            value=int(st.session_state.get("ocr_threshold", 50)),
            step=10,
            help=t("ocr_threshold_help", workspace_id),
        )
        st.markdown(f"#### {t('prompt_version', workspace_id)}")
        prompt_version = st.selectbox(
            t("prompt_version_label", workspace_id),
            options=["v1"],
            index=0,
            help=t("prompt_version_help", workspace_id),
        )
        st.markdown(f"#### {t('language', workspace_id)}")
        ui_language_options = ["en", "zh"]
        ui_language_default = (
            get_setting(workspace_id, "ui_language")
            or st.session_state.get("ui_language")
            or get_setting(None, "ui_language")
            or "en"
        )
        ui_language = st.selectbox(
            t("ui_language", workspace_id),
            options=ui_language_options,
            index=ui_language_options.index(
                "zh" if str(ui_language_default).lower().startswith("zh") else "en"
            ),
            format_func=lambda value: t(
                "chinese" if value == "zh" else "english", workspace_id
            ),
            help=t("ui_language_help", workspace_id),
        )
        output_language_options = ["en", "zh"]
        output_language_default = (
            get_setting(workspace_id, "output_language")
            or st.session_state.get("output_language")
            or get_setting(None, "output_language")
            or "en"
        )
        output_language = st.selectbox(
            t("output_language", workspace_id),
            options=output_language_options,
            index=output_language_options.index(
                "zh" if str(output_language_default).lower().startswith("zh") else "en"
            ),
            format_func=lambda value: t(
                "chinese" if value == "zh" else "english", workspace_id
            ),
            help=t("output_language_help", workspace_id),
        )
        st.markdown(f"#### {t('theme_label', workspace_id)}")
        theme = st.selectbox(
            t("theme_label", workspace_id),
            options=["light", "dark"],
            index=["light", "dark"].index(
                st.session_state.get("ui_theme", "light") or "light"
            ),
            format_func=lambda value: t(f"theme_{value}", workspace_id),
            help=t("theme_help", workspace_id),
        )

        def _save_settings() -> None:
            st.session_state["llm_base_url"] = base_url
            st.session_state["llm_model"] = model
            st.session_state["llm_api_key"] = api_key
            st.session_state["llm_temperature"] = temperature
            st.session_state["api_mode"] = mode
            st.session_state["api_base_url"] = api_base_url
            st.session_state["ocr_mode"] = ocr_mode
            st.session_state["ocr_threshold"] = ocr_threshold
            st.session_state["prompt_version"] = prompt_version
            st.session_state["ui_language"] = ui_language
            st.session_state["output_language"] = output_language
            st.session_state["ui_theme"] = theme
            if embed_model:
                os.environ["STUDYFLOW_EMBED_MODEL"] = embed_model
            if base_url:
                set_setting(None, "llm_base_url", base_url)
            if model:
                set_setting(None, "llm_model", model)
            if api_key:
                set_setting(None, "llm_api_key", api_key)
            set_setting(None, "llm_temperature", str(temperature))
            set_setting(None, "api_mode", mode)
            set_setting(None, "api_base_url", api_base_url)
            set_setting(None, "ocr_mode", ocr_mode)
            set_setting(None, "ocr_threshold", str(ocr_threshold))
            set_setting(None, "prompt_version", prompt_version)
            set_setting(None, "ui_language", ui_language)
            set_setting(None, "output_language", output_language)
            set_setting(None, "ui_theme", theme)
            if workspace_id:
                set_setting(workspace_id, "ui_language", ui_language)
                set_setting(workspace_id, "output_language", output_language)

        st.divider()

        st.markdown(f"#### {t('connection_tests', workspace_id)}")
        if st.button(t("ping_api", workspace_id), disabled=locked, help=lock_msg or None):
            try:
                token = os.getenv("API_TOKEN", "")
                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(
                    f"{api_base_url.rstrip('/')}/health", headers=headers, timeout=10
                )
                if resp.status_code >= 400:
                    st.error(
                        t("api_error", workspace_id).format(
                            status=resp.status_code, text=resp.text
                        )
                    )
                else:
                    st.success(
                        t("api_responded", workspace_id).format(response=resp.json())
                    )
            except requests.RequestException as exc:
                st.error(t("api_ping_failed", workspace_id).format(error=exc))
        if st.button(t("test_llm", workspace_id), disabled=locked, help=lock_msg or None):
            from service.chat_service import ChatConfigError, chat

            try:
                response = chat(
                    prompt=t("llm_test_prompt", workspace_id),
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    temperature=0.1,
                )
                st.success(
                    t("llm_responded", workspace_id).format(
                        response=response[:120]
                    )
                )
            except ChatConfigError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(t("llm_test_failed", workspace_id).format(error=exc))

        if st.button(t("test_embedding", workspace_id), disabled=locked, help=lock_msg or None):
            from core.retrieval.embedder import (
                EmbeddingError,
                build_embedding_settings,
                embed_texts,
            )

            try:
                settings = build_embedding_settings()
                embed_texts(["ping"], settings)
                st.success(t("embedding_loaded", workspace_id))
            except EmbeddingError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(t("embedding_test_failed", workspace_id).format(error=exc))

    with right:
        st.markdown(f"### {t('storage', workspace_id)}")
        workspace_dir = get_workspaces_dir()
        st.code(str(workspace_dir))
        if workspace_id:
            st.caption(t("active_workspace", workspace_id).format(workspace=workspace_id))
            st.caption(
                t("indexes_path", workspace_id).format(
                    path=f"{workspace_dir}/{workspace_id}/index/"
                )
            )
            st.caption(
                t("runs_path", workspace_id).format(
                    path=f"{workspace_dir}/{workspace_id}/runs/"
                )
            )
            st.caption(
                t("outputs_path", workspace_id).format(
                    path=f"{workspace_dir}/{workspace_id}/outputs/"
                )
            )
        st.caption(t("backup_tip", workspace_id))
        if os.getenv("STUDYFLOW_DEV_MODE", "").lower() in {"1", "true", "yes", "on"}:
            st.divider()
            if st.button(
                t("reset_demo_projects", workspace_id),
                disabled=locked,
                help=lock_msg or None,
            ):
                import shutil
                from pathlib import Path

                from service.workspace_service import create_workspace, delete_workspace, list_workspaces

                keep_name = "test1"
                workspaces = list_workspaces()
                keep_ids = [ws["id"] for ws in workspaces if ws["name"] == keep_name]
                if not keep_ids:
                    keep_ids = [create_workspace(keep_name)]
                for ws in workspaces:
                    if ws["id"] in keep_ids:
                        continue
                    delete_workspace(ws["id"])
                    target = Path(workspace_dir) / ws["id"]
                    if workspace_dir in target.resolve().parents and target.exists():
                        shutil.rmtree(target)
                st.success(t("reset_demo_done", workspace_id))
        st.markdown(f"### {t('retrieval_mode', workspace_id)}")
        retrieval_options = ["vector", "bm25", "hybrid"]
        stored_mode = get_setting(workspace_id, "retrieval_mode") if workspace_id else None
        current_mode = stored_mode if stored_mode in retrieval_options else "vector"
        mode = st.selectbox(
            t("default_mode", workspace_id),
            options=retrieval_options,
            index=retrieval_options.index(current_mode),
        )
        if workspace_id and st.button(
            t("save_retrieval_mode", workspace_id), disabled=locked, help=lock_msg or None
        ):
            set_setting(workspace_id, "retrieval_mode", mode)
            st.session_state["retrieval_mode"] = mode
            st.success(t("retrieval_mode_saved", workspace_id))

        if st.button(
            t("save_settings", workspace_id),
            disabled=locked,
            help=lock_msg or None,
            type="primary",
        ):
            _save_settings()
            st.success(t("settings_saved", workspace_id))
        if st.button(t("back_to_start", workspace_id)):
            st.session_state["active_nav"] = "Start"
            st.rerun()
