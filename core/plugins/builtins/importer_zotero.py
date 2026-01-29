from __future__ import annotations

from pathlib import Path

from core.external.sources import create_source, find_source, get_mapping, list_mappings, touch_source, upsert_mapping
from core.external.zotero import list_pdf_attachments
from core.plugins.base import PluginBase, PluginContext, PluginResult
from infra.db import get_workspaces_dir
from service.document_service import set_document_source
from service.ingest_service import IngestError
from service.paper_service import ensure_paper, extract_paper_metadata
from service.tasks_service import enqueue_ingest_task, run_task_by_id


class ImportZoteroPlugin(PluginBase):
    name = "importer_zotero"
    version = "1.0.0"
    description = "Import Zotero library PDFs from a data directory."

    def run(self, context: PluginContext) -> PluginResult:
        data_dir = context.args.get("data_dir")
        if not data_dir:
            return PluginResult(ok=False, message="Missing Zotero data dir.")
        copy_mode = context.args.get("copy", True)
        ocr_mode = context.args.get("ocr_mode", "off")
        ocr_threshold = int(context.args.get("ocr_threshold", 50))
        doc_type = context.args.get("doc_type", "paper")

        root = Path(data_dir)
        if not root.exists():
            return PluginResult(ok=False, message="Zotero data dir not found.")

        source = find_source(
            workspace_id=context.workspace_id,
            source_type="zotero",
            params={"data_dir": str(root)},
        )
        source_id = source.id if source else create_source(
            workspace_id=context.workspace_id,
            source_type="zotero",
            params={"data_dir": str(root)},
        )

        attachments = list_pdf_attachments(root)
        if not attachments:
            return PluginResult(ok=True, message="No Zotero PDF attachments found.")

        seen_keys = {(att.item_key, att.attachment_key) for att in attachments}
        for mapping in list_mappings(source_id):
            key = (mapping.external_id, mapping.external_sub_id or "")
            if key not in seen_keys and mapping.status != "missing":
                upsert_mapping(
                    source_id=source_id,
                    external_id=mapping.external_id,
                    external_sub_id=mapping.external_sub_id,
                    doc_id=mapping.doc_id,
                    status="missing",
                )

        docs_dir = get_workspaces_dir() / context.workspace_id / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        imported = 0
        skipped = 0
        for attachment in attachments:
            mapping = get_mapping(
                source_id=source_id,
                external_id=attachment.item_key,
                external_sub_id=attachment.attachment_key,
            )
            if mapping and mapping.status == "ok":
                skipped += 1
                continue
            try:
                target_path = docs_dir / attachment.file_path.name
                if not copy_mode:
                    if not target_path.exists():
                        target_path.symlink_to(attachment.file_path)
                task_id = enqueue_ingest_task(
                    workspace_id=context.workspace_id,
                    path=str(attachment.file_path),
                    ocr_mode=ocr_mode,
                    ocr_threshold=ocr_threshold,
                    doc_type=doc_type,
                    save_dir=str(docs_dir),
                    write_file=copy_mode,
                    existing_path=str(target_path) if not copy_mode else None,
                )
                task_result = run_task_by_id(task_id)
                result_doc_id = task_result["doc_id"]
                set_document_source(
                    doc_id=result_doc_id,
                    source_type="zotero",
                    source_ref=attachment.item_key,
                )
                try:
                    metadata = extract_paper_metadata(Path(target_path))
                    ensure_paper(
                        workspace_id=context.workspace_id,
                        doc_id=result_doc_id,
                        metadata=metadata,
                    )
                except Exception:
                    pass
                upsert_mapping(
                    source_id=source_id,
                    external_id=attachment.item_key,
                    external_sub_id=attachment.attachment_key,
                    doc_id=result_doc_id,
                    status="ok",
                    meta={"filename": attachment.file_path.name},
                )
                imported += 1
            except IngestError:
                upsert_mapping(
                    source_id=source_id,
                    external_id=attachment.item_key,
                    external_sub_id=attachment.attachment_key,
                    doc_id=None,
                    status="error",
                )
                continue
        touch_source(source_id)
        return PluginResult(
            ok=True,
            message=f"Imported {imported} PDFs. Skipped {skipped}.",
            data={"imported": imported, "skipped": skipped},
        )
