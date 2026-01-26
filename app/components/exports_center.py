from __future__ import annotations

import streamlit as st

from service.bundle_service import bundle_export, bundle_import
from service.pack_service import make_pack, PackServiceError
from app.ui.locks import running_task_summary


def render_exports_center(*, workspace_id: str | None) -> None:
    st.markdown("### Exports")
    if not workspace_id:
        st.info("Select a project to export or import.")
        return
    locked, lock_msg = running_task_summary(workspace_id)
    if lock_msg:
        st.info(lock_msg)

    with st.expander("Workspace Bundle"):
        with_pdf = st.checkbox("Include PDFs", value=True)
        with_assets = st.checkbox("Include assets", value=True)
        with_prompts = st.checkbox("Include prompts", value=True)
        out_path = st.text_input("Output path (optional)")
        if st.button("Export bundle", disabled=locked, help=lock_msg or None):
            path = bundle_export(
                workspace_id=workspace_id,
                out_path=out_path or None,
                with_pdf=with_pdf,
                with_assets=with_assets,
                with_prompts=with_prompts,
            )
            st.success(f"Bundle exported: {path}")

        st.divider()
        import_path = st.text_input("Import bundle path")
        rebuild_index = st.checkbox("Rebuild index after import", value=True)
        if st.button(
            "Import bundle",
            disabled=locked or not import_path.strip(),
            help=lock_msg or None,
        ):
            new_workspace = bundle_import(path=import_path.strip(), rebuild_index=rebuild_index)
            st.success(f"Bundle imported into workspace: {new_workspace}")

    with st.expander("Submission Pack"):
        pack_type = st.selectbox(
            "Pack type",
            options=["slides", "exam", "related"],
            format_func=lambda value: value.upper(),
        )
        source_id = st.text_input("Source ID (document/course/project ID)")
        if st.button(
            "Build pack",
            disabled=locked or not source_id.strip(),
            help=lock_msg or None,
        ):
            try:
                path = make_pack(
                    workspace_id=workspace_id,
                    pack_type=pack_type,
                    source_id=source_id.strip(),
                )
                st.success(f"Pack created: {path}")
            except PackServiceError as exc:
                st.error(str(exc))
