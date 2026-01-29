from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.ui.components import card_footer, card_header, render_inspector
from app.ui.i18n import t
from app.ui.locks import running_task_summary
from core.ingest.ocr import OCRSettings, ocr_available
from core.ui_state.guards import llm_ready
from core.ui_state.storage import get_setting
from infra.db import get_workspaces_dir
from service.api_mode_adapter import ApiModeAdapter
from service.document_service import normalize_doc_type
from service.recent_activity_service import list_recent_activity
from service.tasks_service import enqueue_ingest_index_task, run_task_in_background


def _get_demo_pdf_path() -> Path | None:
    """Find the demo PDF in the examples directory."""
    # Try multiple locations for the demo PDF
    candidates = [
        Path(__file__).parent.parent.parent / "examples" / "ml_fundamentals.pdf",
        Path("examples") / "ml_fundamentals.pdf",
        Path("/app/examples") / "ml_fundamentals.pdf",  # Docker path
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_demo_data(workspace_id: str) -> str | None:
    """Load demo PDF into the workspace and trigger processing."""
    demo_path = _get_demo_pdf_path()
    if not demo_path:
        return None

    # Copy demo PDF to workspace uploads
    upload_dir = get_workspaces_dir() / workspace_id / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / demo_path.name

    if not target_path.exists():
        target_path.write_bytes(demo_path.read_bytes())

    # Enqueue ingest + index task
    task_id = enqueue_ingest_index_task(
        workspace_id=workspace_id,
        path=str(target_path),
        ocr_mode="off",
        ocr_threshold=50,
        doc_type="course",
        save_dir=str(upload_dir),
        write_file=False,  # Already written
    )
    run_task_in_background(task_id)
    return task_id


def _setup_checks(workspace_id: str | None) -> dict:
    if st.session_state.get("api_mode") == "api":
        llm_ok, llm_reason = True, ""
    else:
        llm_ok, llm_reason = llm_ready(
            st.session_state.get("llm_base_url", ""),
            st.session_state.get("llm_model", ""),
            st.session_state.get("llm_api_key", ""),
        )
    retrieval_mode = get_setting(workspace_id, "retrieval_mode") or st.session_state.get(
        "retrieval_mode", ""
    )
    retrieval_ok = retrieval_mode in {"vector", "bm25", "hybrid", "auto"}
    ocr_ok, ocr_reason = ocr_available(OCRSettings())
    workspace_dir = get_workspaces_dir()
    workspace_ok = workspace_dir.exists() and workspace_dir.is_dir()
    return {
        "llm_ok": llm_ok,
        "llm_reason": llm_reason,
        "retrieval_ok": retrieval_ok,
        "ocr_ok": ocr_ok,
        "ocr_reason": ocr_reason,
        "workspace_ok": workspace_ok,
        "workspace_path": str(workspace_dir),
    }


def render_start_page(
    *,
    main_col: st.delta_generator.DeltaGenerator,
    inspector_col: st.delta_generator.DeltaGenerator,
    workspace_id: str | None,
    api_adapter: ApiModeAdapter,
) -> None:
    with main_col:
        st.markdown(f"## {t('start_title', workspace_id)}")
        st.caption(t("start_caption", workspace_id))

        if not workspace_id:
            st.info(t("start_select_project", workspace_id))
            return

        setup = _setup_checks(workspace_id)
        locked, lock_msg = running_task_summary(workspace_id)
        if lock_msg:
            st.info(lock_msg)

        setup_ok = setup["llm_ok"] and setup["retrieval_ok"] and setup["workspace_ok"]
        st.markdown(f"### {t('setup_checklist', workspace_id)}")
        setup_cols = st.columns(5)
        setup_cols[0].metric(t("setup_llm", workspace_id), "OK" if setup["llm_ok"] else "Missing")
        setup_cols[1].metric(
            t("setup_retrieval", workspace_id),
            "OK" if setup["retrieval_ok"] else "Missing",
        )
        setup_cols[2].metric(
            t("setup_ocr", workspace_id),
            "OK" if setup["ocr_ok"] else "Unavailable",
        )
        setup_cols[3].metric(
            t("setup_workspace", workspace_id),
            "OK" if setup["workspace_ok"] else "Missing",
        )
        setup_cols[4].write("")
        st.caption(f"{t('workspace_path', workspace_id)}: {setup['workspace_path']}")
        if not setup["llm_ok"]:
            st.warning(setup["llm_reason"])
        if not setup["ocr_ok"] and setup["ocr_reason"]:
            st.caption(setup["ocr_reason"])
        if not setup_ok:
            st.warning(t("setup_incomplete", workspace_id))

        # Setup action buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button(t("open_settings", workspace_id), type="primary", use_container_width=True):
                st.session_state["active_nav"] = "Tools"
                st.session_state["tools_tab"] = "settings"
                st.rerun()
        with btn_col2:
            demo_available = _get_demo_pdf_path() is not None
            if st.button(
                t("load_demo_data", workspace_id),
                type="secondary",
                disabled=locked or not demo_available,
                help=lock_msg if locked else (None if demo_available else t("demo_not_found", workspace_id)),
                use_container_width=True,
            ):
                task_id = _load_demo_data(workspace_id)
                if task_id:
                    st.success(t("demo_loading", workspace_id))
                    st.rerun()
                else:
                    st.error(t("demo_not_found", workspace_id))
        with btn_col3:
            if st.button(
                t("run_doctor", workspace_id),
                type="secondary",
                disabled=locked,
                help=lock_msg or None,
                use_container_width=True,
            ):
                st.session_state["active_nav"] = "Tools"
                st.session_state["tools_tab"] = "diagnostics"
                st.rerun()

        st.divider()
        col_a, col_b, col_c = st.columns(3, gap="large")
        with col_a:
            card_header(
                t("import_auto_title", workspace_id),
                t("import_auto_subtitle", workspace_id),
            )
            default_type = st.session_state.get("last_doc_type", "course")
            doc_type = st.selectbox(
                t("doc_type_label", workspace_id),
                options=["course", "paper", "other"],
                index=["course", "paper", "other"].index(
                    normalize_doc_type(default_type)
                ),
                format_func=lambda value: t(f"doc_type_{value}", workspace_id),
            )
            if st.button(
                t("open_import", workspace_id),
                disabled=locked or not setup["workspace_ok"],
                help=lock_msg or None,
            ):
                st.session_state["library_doc_type"] = doc_type
                st.session_state["active_nav"] = "Library"
                st.session_state["last_doc_type"] = doc_type
                st.rerun()
            card_footer()

        with col_b:
            card_header(
                t("ask_title", workspace_id),
                t("ask_subtitle", workspace_id),
            )
            if st.button(
                t("open_ask", workspace_id),
                disabled=locked or not setup["llm_ok"],
                help=lock_msg or setup.get("llm_reason") or None,
            ):
                st.session_state["active_nav"] = "Library"
                st.rerun()
            card_footer()

        with col_c:
            card_header(
                t("generate_title", workspace_id),
                t("generate_subtitle", workspace_id),
            )
            if st.button(
                t("open_create_course", workspace_id),
                disabled=locked or not setup_ok,
                help=lock_msg or setup.get("llm_reason") or None,
            ):
                st.session_state["active_nav"] = "Create"
                st.session_state["create_tab"] = "course"
                st.rerun()
            if st.button(
                t("open_create_paper", workspace_id),
                disabled=locked or not setup_ok,
                help=lock_msg or setup.get("llm_reason") or None,
            ):
                st.session_state["active_nav"] = "Create"
                st.session_state["create_tab"] = "paper"
                st.rerun()
            if st.button(
                t("open_create_slides", workspace_id),
                disabled=locked or not setup_ok,
                help=lock_msg or setup.get("llm_reason") or None,
            ):
                st.session_state["active_nav"] = "Create"
                st.session_state["create_tab"] = "presentation"
                st.rerun()
            card_footer()

        st.divider()
        st.markdown(f"### {t('recent_activity', workspace_id)}")
        activity = list_recent_activity(workspace_id, limit=10)
        if not activity:
            st.caption(t("no_recent_activity", workspace_id))
        else:
            selected = st.selectbox(
                t("recent_activity", workspace_id),
                options=[entry["id"] for entry in activity],
                format_func=lambda entry_id: next(
                    (
                        f"{entry['created_at']} · {entry['type']} · {entry.get('title') or '-'}"
                        for entry in activity
                        if entry["id"] == entry_id
                    ),
                    entry_id,
                ),
            )
            if st.button(t("open_recent_activity", workspace_id)):
                st.session_state["active_nav"] = "Tools"
                st.session_state["tools_tab"] = "recent_activity"
                st.session_state["recent_activity_selected_id"] = selected
                st.rerun()

    with inspector_col:
        if not workspace_id:
            return
        render_inspector(
            status={t("project", workspace_id): workspace_id},
            citations=None,
            history=None,
        )
