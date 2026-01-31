from __future__ import annotations

import streamlit as st

from app.ui.i18n import t
from app.ui.locks import running_task_summary
from service.bundle_service import bundle_export, bundle_import
from service.pack_service import PackServiceError, make_pack


def render_exports_center(*, workspace_id: str | None) -> None:
    st.markdown(f"### {t('exports_center_title', workspace_id)}")
    if not workspace_id:
        st.info(t("exports_select_project", workspace_id))
        return
    locked, lock_msg = running_task_summary(workspace_id)
    if lock_msg:
        st.info(lock_msg)

    with st.expander(t("workspace_bundle", workspace_id)):
        with_pdf = st.checkbox(t("include_pdfs", workspace_id), value=True)
        with_assets = st.checkbox(t("include_assets", workspace_id), value=True)
        with_prompts = st.checkbox(t("include_prompts", workspace_id), value=True)
        out_path = st.text_input(t("output_path_optional", workspace_id))
        if st.button(t("export_bundle", workspace_id), disabled=locked, help=lock_msg or None):
            path = bundle_export(
                workspace_id=workspace_id,
                out_path=out_path or None,
                with_pdf=with_pdf,
                with_assets=with_assets,
                with_prompts=with_prompts,
            )
            st.success(t("bundle_exported", workspace_id).format(path=path))

        st.divider()
        import_path = st.text_input(t("import_bundle_path", workspace_id))
        rebuild_index = st.checkbox(t("rebuild_index_after_import", workspace_id), value=True)
        if st.button(
            t("import_bundle", workspace_id),
            disabled=locked or not import_path.strip(),
            help=lock_msg or None,
        ):
            new_workspace = bundle_import(path=import_path.strip(), rebuild_index=rebuild_index)
            st.success(
                t("bundle_imported", workspace_id).format(workspace=new_workspace)
            )

    with st.expander(t("submission_pack", workspace_id)):
        pack_type = st.selectbox(
            t("pack_type", workspace_id),
            options=["slides", "exam", "related"],
            format_func=lambda value: t(f"pack_type_{value}", workspace_id),
        )
        source_id = st.text_input(t("pack_source_id", workspace_id))
        if st.button(
            t("build_pack", workspace_id),
            disabled=locked or not source_id.strip(),
            help=lock_msg or None,
        ):
            try:
                path = make_pack(
                    workspace_id=workspace_id,
                    pack_type=pack_type,
                    source_id=source_id.strip(),
                )
                st.success(t("pack_created", workspace_id).format(path=path))
            except PackServiceError as exc:
                st.error(str(exc))
