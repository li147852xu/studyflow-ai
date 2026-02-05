from __future__ import annotations

import os

import streamlit as st

from app.ui.components import render_empty_state, render_header_card, render_section_with_help
from app.ui.labels import L
from core.ui_state.storage import get_setting, set_setting


def _load_setting(workspace_id: str | None, key: str, default: str = "") -> str:
    value = get_setting(workspace_id, key)
    return value if value is not None else default


def _save_settings(
    *,
    workspace_id: str | None,
    llm_base_url: str,
    llm_model: str,
    llm_api_key: str,
    retrieval_mode: str,
    map_tokens: int,
    reduce_tokens: int,
    theme: str,
    language: str,
    output_language: str,
) -> None:
    set_setting(workspace_id, "llm_base_url", llm_base_url)
    set_setting(workspace_id, "llm_model", llm_model)
    set_setting(workspace_id, "llm_api_key", llm_api_key)
    set_setting(workspace_id, "retrieval_mode", retrieval_mode)
    set_setting(workspace_id, "rag_map_tokens", str(map_tokens))
    set_setting(workspace_id, "rag_reduce_tokens", str(reduce_tokens))
    set_setting(workspace_id, "ui_theme", theme)
    set_setting(workspace_id, "ui_language", language)
    set_setting(workspace_id, "output_language", output_language)
    os.environ["STUDYFLOW_LLM_BASE_URL"] = llm_base_url
    os.environ["STUDYFLOW_LLM_MODEL"] = llm_model
    os.environ["STUDYFLOW_LLM_API_KEY"] = llm_api_key
    st.session_state["ui_theme"] = theme
    st.session_state["ui_language"] = language
    st.session_state["output_language"] = output_language
    st.session_state["llm_base_url"] = llm_base_url
    st.session_state["llm_model"] = llm_model
    st.session_state["llm_api_key"] = llm_api_key
    st.session_state["retrieval_mode"] = retrieval_mode


def render_settings(*, main_col, inspector_col, workspace_id: str | None) -> None:
    with main_col:
        render_section_with_help(L("设置", "Settings"), "settings")

        if not workspace_id:
            render_empty_state(
                "⚙️",
                L("请选择工作区", "Select a Workspace"),
                L("在侧边栏选择或创建工作区以配置设置。", "Select or create a workspace in the sidebar to configure settings."),
            )
            return

        render_header_card(
            L("系统设置", "System Settings"),
            L("所有设置仅保存在本地，不会上传到云端", "All settings are stored locally and never uploaded to the cloud"),
        )

        # Top save button - prominent
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            save_top = st.button(
                L("💾 保存所有设置", "💾 Save All Settings"),
                key="btn_save_settings_top",
                type="primary",
                use_container_width=True,
            )

        st.markdown("")  # Spacing

        # LLM Settings Section
        st.markdown(
            f"""
            <div style="
                background: var(--surface-bg);
                border-radius: var(--radius-lg);
                padding: var(--space-lg);
                margin-bottom: var(--space-lg);
                border: 1px solid var(--card-border);
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 1.5rem;">🤖</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem; color: var(--text-color);">{L('大语言模型', 'LLM Configuration')}</div>
                        <div style="font-size: 0.85rem; color: var(--muted-text);">{L('配置 AI 模型提供商和参数', 'Configure AI model provider and parameters')}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")  # This will be replaced by the actual form below

        col1, col2 = st.columns(2)
        with col1:
            llm_base_url = st.text_input(
                L("API 地址", "API Base URL"),
                value=_load_setting(workspace_id, "llm_base_url"),
                placeholder="https://api.openai.com/v1",
                help=L("OpenAI 兼容接口地址。", "OpenAI-compatible base URL."),
                key="settings_llm_base_url",
            )
        with col2:
            llm_model = st.text_input(
                L("模型名称", "Model Name"),
                value=_load_setting(workspace_id, "llm_model"),
                placeholder="gpt-4o-mini",
                help=L("对话模型名称。", "Chat model name."),
                key="settings_llm_model",
            )

        llm_api_key = st.text_input(
            L("API 密钥", "API Key"),
            value=_load_setting(workspace_id, "llm_api_key"),
            type="password",
            placeholder="sk-...",
            help=L("🔒 仅保存在本地工作区数据库，不会提交到代码仓库。", "🔒 Stored locally in workspace DB, never committed to repo."),
            key="settings_llm_api_key",
        )

        st.divider()

        # Retrieval Settings
        st.markdown(f"### 🔍 {L('检索配置', 'Retrieval Configuration')}")
        st.caption(L("配置文档检索和 RAG 参数。", "Configure document retrieval and RAG parameters."))

        col1, col2, col3 = st.columns(3)

        with col1:
            stored_mode = _load_setting(workspace_id, "retrieval_mode", "hybrid")
            try:
                mode_index = ["vector", "bm25", "hybrid"].index(stored_mode)
            except ValueError:
                mode_index = 2
            retrieval_mode = st.selectbox(
                L("检索模式", "Retrieval Mode"),
                options=["vector", "bm25", "hybrid"],
                index=mode_index,
                format_func=lambda x: {
                    "vector": L("向量检索", "Vector"),
                    "bm25": L("关键词检索", "BM25"),
                    "hybrid": L("混合检索", "Hybrid"),
                }.get(x, x),
                help=L("混合模式通常效果最佳。", "Hybrid mode usually works best."),
                key="settings_retrieval_mode",
            )

        with col2:
            map_tokens = st.number_input(
                L("Map 预算", "Map Tokens"),
                min_value=50,
                max_value=1000,
                value=int(_load_setting(workspace_id, "rag_map_tokens", "250")),
                help=L("每个文档的 token 预算。", "Token budget per document."),
                key="settings_map_tokens",
            )

        with col3:
            reduce_tokens = st.number_input(
                L("Reduce 预算", "Reduce Tokens"),
                min_value=100,
                max_value=2000,
                value=int(_load_setting(workspace_id, "rag_reduce_tokens", "600")),
                help=L("最终汇总的 token 预算。", "Token budget for final summary."),
                key="settings_reduce_tokens",
            )

        st.divider()

        # Theme & Language
        st.markdown(f"### 🎨 {L('外观与语言', 'Appearance & Language')}")
        st.caption(L("个性化界面设置。", "Personalize the interface."))

        col1, col2, col3 = st.columns(3)

        with col1:
            stored_theme = _load_setting(workspace_id, "ui_theme", "light")
            theme = st.selectbox(
                L("主题", "Theme"),
                options=["light", "dark"],
                index=0 if stored_theme == "light" else 1,
                format_func=lambda x: {
                    "light": f"☀️ {L('浅色', 'Light')}",
                    "dark": f"🌙 {L('深色', 'Dark')}",
                }.get(x, x),
                key="settings_theme",
            )

        with col2:
            stored_lang = _load_setting(workspace_id, "ui_language", "en")
            language = st.selectbox(
                L("界面语言", "UI Language"),
                options=["en", "zh"],
                index=0 if stored_lang == "en" else 1,
                format_func=lambda x: {
                    "en": "🇺🇸 English",
                    "zh": "🇨🇳 中文",
                }.get(x, x),
                key="settings_language",
                help=L("控制界面显示语言。", "Controls UI display language."),
            )

        with col3:
            stored_output_lang = _load_setting(workspace_id, "output_language", "en")
            output_language = st.selectbox(
                L("输出语言", "Output Language"),
                options=["en", "zh"],
                index=0 if stored_output_lang == "en" else 1,
                format_func=lambda x: {
                    "en": "🇺🇸 English",
                    "zh": "🇨🇳 中文",
                }.get(x, x),
                key="settings_output_language",
                help=L("控制 AI 生成内容的语言（课程概览、速记表等）。", "Controls the language of AI-generated content (overview, cheatsheet, etc.)."),
            )

        st.divider()

        # Bottom save button
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            save_bottom = st.button(
                L("保存设置", "Save Settings"),
                key="btn_save_settings_bottom",
                type="primary",
                use_container_width=True,
            )

        # Handle save
        if save_top or save_bottom:
            _save_settings(
                workspace_id=workspace_id,
                llm_base_url=llm_base_url.strip(),
                llm_model=llm_model.strip(),
                llm_api_key=llm_api_key.strip(),
                retrieval_mode=retrieval_mode,
                map_tokens=int(map_tokens),
                reduce_tokens=int(reduce_tokens),
                theme=theme,
                language=language,
                output_language=output_language,
            )
            st.success(L("✓ 设置已保存！刷新页面以应用主题更改。", "✓ Settings saved! Refresh the page to apply theme changes."))
            st.rerun()

    with inspector_col:
        st.markdown(f"### {L('配置状态', 'Configuration Status')}")

        # Check LLM configuration
        llm_key = _load_setting(workspace_id, "llm_api_key")
        llm_model_name = _load_setting(workspace_id, "llm_model")

        # LLM Status Card
        if llm_key and llm_model_name:
            st.markdown(
                f"""
                <div style="
                    background: var(--success-light);
                    border: 1px solid var(--success-color);
                    border-radius: var(--radius-md);
                    padding: var(--space-md);
                    margin-bottom: var(--space-sm);
                ">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>✅</span>
                        <span style="font-weight: 600; color: var(--success-color);">{L('LLM 已配置', 'LLM Configured')}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--muted-text); margin-top: 4px;">{llm_model_name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="
                    background: var(--warning-light);
                    border: 1px solid var(--warning-color);
                    border-radius: var(--radius-md);
                    padding: var(--space-md);
                    margin-bottom: var(--space-sm);
                ">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>⚠️</span>
                        <span style="font-weight: 600; color: var(--warning-color);">{L('LLM 未配置', 'LLM Not Configured')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")  # Spacing

        # Settings summary
        st.markdown(f"#### {L('当前配置', 'Current Settings')}")

        settings_items = [
            ("🔍", L("检索模式", "Retrieval"), _load_setting(workspace_id, "retrieval_mode", "hybrid")),
            ("🎨", L("主题", "Theme"), _load_setting(workspace_id, "ui_theme", "light")),
            ("🌐", L("界面语言", "UI Lang"), _load_setting(workspace_id, "ui_language", "en")),
            ("📝", L("输出语言", "Output Lang"), _load_setting(workspace_id, "output_language", "en")),
        ]

        for icon, label, value in settings_items:
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
                    border-bottom: 1px solid var(--card-border);
                ">
                    <span style="color: var(--muted-text); font-size: 0.9rem;">{icon} {label}</span>
                    <span style="
                        background: var(--surface-bg);
                        padding: 2px 10px;
                        border-radius: var(--radius-full);
                        font-size: 0.85rem;
                        font-weight: 500;
                        color: var(--text-color);
                    ">{value}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")  # Spacing

        # Tips section
        st.markdown(f"#### {L('提示', 'Tips')}")
        tips = [
            L("API 密钥仅保存在本地", "API keys are stored locally only"),
            L("混合检索模式通常效果最佳", "Hybrid retrieval usually works best"),
            L("更改主题后需刷新页面", "Refresh page after theme change"),
        ]
        for tip in tips:
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    padding: 6px 0;
                    font-size: 0.85rem;
                    color: var(--muted-text);
                ">
                    <span>•</span>
                    <span>{tip}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
