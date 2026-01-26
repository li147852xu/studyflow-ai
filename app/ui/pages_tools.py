from __future__ import annotations

import streamlit as st

from app.ui.components import render_inspector, section_title, run_with_progress
from app.ui.i18n import t
from core.ui_state.guards import llm_ready
from service.coach_service import list_coach_sessions, start_coach, submit_coach, show_coach_session
from service.retrieval_service import index_status
from app.components.tasks_center import render_tasks_center
from app.components.exports_center import render_exports_center
from app.components.plugins_center import render_plugins_center
from app.components.diagnostics_center import render_diagnostics_center
from app.components.settings_center import render_settings_center
from app.components.recent_activity_view import render_recent_activity


def render_tools_page(
    *,
    main_col: st.delta_generator.DeltaGenerator,
    inspector_col: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
) -> None:
    with main_col:
        st.markdown(f"## {t('tools_title', workspace_id)}")
        st.caption(t("tools_caption", workspace_id))

        if not workspace_id:
            st.info(t("tools_select_project", workspace_id))
            return
        model_name = st.session_state.get("llm_model") or t("model_unknown", workspace_id)

        tab_keys = [
            "coach",
            "tasks",
            "exports",
            "plugins",
            "diagnostics",
            "recent_activity",
            "settings",
        ]
        selected_tab = st.radio(
            t("tools_tabs", workspace_id),
            options=tab_keys,
            index=tab_keys.index(st.session_state.get("tools_tab", "coach"))
            if st.session_state.get("tools_tab", "coach") in tab_keys
            else 0,
            format_func=lambda value: t(f"tabs_{value}", workspace_id),
            horizontal=True,
            label_visibility="collapsed",
        )
        st.session_state["tools_tab"] = selected_tab
        inspector_payload = {t("project", workspace_id): workspace_id}
        citations = None

        def _resolve_mode() -> str:
            mode = st.session_state.get("retrieval_mode", "auto")
            if mode != "auto" or not workspace_id:
                return mode
            status = index_status(workspace_id)
            return "hybrid" if status.get("vector_count", 0) > 0 else "bm25"

        if selected_tab == "coach":
            section_title(t("study_coach", workspace_id))
            ready, reason = llm_ready(
                st.session_state.get("llm_base_url", ""),
                st.session_state.get("llm_model", ""),
                st.session_state.get("llm_api_key", ""),
            )
            problem = st.text_area(
                t("problem_statement", workspace_id),
                height=140,
                key="tools_coach_problem",
            )
            if st.button(
                t("start_coaching", workspace_id),
                disabled=not problem.strip() or not ready,
                help=reason,
            ):
                def _work() -> None:
                    result = start_coach(
                        workspace_id=workspace_id,
                        problem=problem.strip(),
                        retrieval_mode=_resolve_mode(),
                    )
                    st.session_state["tools_coach_session_id"] = result.session.id
                    st.session_state["tools_coach_output"] = result.output
                    st.success(t("phase_a_complete", workspace_id))
                    st.write(result.output.content)

                ok, _ = run_with_progress(
                    label=t("llm_generating", workspace_id).format(model=model_name),
                    work=_work,
                    success_label=t("llm_complete", workspace_id),
                    error_label=t("llm_failed", workspace_id),
                )
                if ok:
                    output = st.session_state.get("tools_coach_output")
                    if output:
                        citations = output.citations

            st.divider()
            section_title(t("coach_review", workspace_id))
            sessions = list_coach_sessions(workspace_id)
            session_ids = [session.id for session in sessions]
            selected_session = st.selectbox(
                t("session", workspace_id),
                options=["(none)"] + session_ids,
                key="tools_coach_session_select",
            )
            answer = st.text_area(
                t("your_answer", workspace_id),
                height=140,
                key="tools_coach_answer",
            )
            if st.button(
                t("submit_answer", workspace_id),
                disabled=selected_session == "(none)" or not answer.strip() or not ready,
                help=reason,
            ):
                def _work() -> None:
                    result = submit_coach(
                        workspace_id=workspace_id,
                        session_id=selected_session,
                        answer=answer.strip(),
                        retrieval_mode=_resolve_mode(),
                    )
                    st.session_state["tools_coach_session_id"] = result.session.id
                    st.session_state["tools_coach_output"] = result.output
                    st.success(t("phase_b_complete", workspace_id))
                    st.write(result.output.content)

                ok, _ = run_with_progress(
                    label=t("llm_generating", workspace_id).format(model=model_name),
                    work=_work,
                    success_label=t("llm_complete", workspace_id),
                    error_label=t("llm_failed", workspace_id),
                )
                if ok:
                    output = st.session_state.get("tools_coach_output")
                    if output:
                        citations = output.citations

        if selected_tab == "tasks":
            render_tasks_center(workspace_id=workspace_id)

        if selected_tab == "exports":
            render_exports_center(workspace_id=workspace_id)

        if selected_tab == "plugins":
            render_plugins_center(workspace_id=workspace_id)

        if selected_tab == "diagnostics":
            render_diagnostics_center(workspace_id=workspace_id)

        if selected_tab == "recent_activity":
            render_recent_activity(workspace_id=workspace_id)

        if selected_tab == "settings":
            render_settings_center(center=st.container(), right=st.container(), workspace_id=workspace_id)

    with inspector_col:
        session_id = st.session_state.get("tools_coach_session_id")
        if session_id:
            session = show_coach_session(session_id)
            inspector_payload.update(
                {
                    t("session", workspace_id): session.id,
                    t("status", workspace_id): session.status or "-",
                    t("updated_at", workspace_id): session.updated_at[:19],
                }
            )
        output = st.session_state.get("tools_coach_output")
        if output and getattr(output, "citations", None):
            citations = output.citations
        render_inspector(status=inspector_payload, citations=citations)
