from __future__ import annotations

import json
from pathlib import Path

from core.external.folder_sync import scan_folder
from core.external.sources import create_source, find_source, touch_source, upsert_mapping, get_mapping, list_mappings
from core.plugins.base import PluginBase, PluginContext, PluginResult
from infra.db import get_workspaces_dir
from service.ingest_service import ingest_pdf, IngestError
from service.document_service import set_document_source


class ImportFolderSyncPlugin(PluginBase):
    name = "importer_folder_sync"
    version = "1.0.0"
    description = "Sync PDFs from a local folder into the workspace."

    def run(self, context: PluginContext) -> PluginResult:
        folder = context.args.get("path")
        if not folder:
            return PluginResult(ok=False, message="Missing path.")
        copy_mode = context.args.get("copy", True)
        ignore_globs = context.args.get("ignore", []) or []
        ocr_mode = context.args.get("ocr_mode", "off")
        ocr_threshold = int(context.args.get("ocr_threshold", 50))

        root = Path(folder)
        if not root.exists():
            return PluginResult(ok=False, message="Folder not found.")

        source = find_source(
            workspace_id=context.workspace_id,
            source_type="folder",
            params={"path": str(root)},
        )
        source_id = source.id if source else create_source(
            workspace_id=context.workspace_id,
            source_type="folder",
            params={"path": str(root)},
        )

        files = scan_folder(root, ignore_globs=ignore_globs)
        if not files:
            return PluginResult(ok=True, message="No PDF files found.", data={"count": 0})

        seen_paths = {str(file.path) for file in files}
        for mapping in list_mappings(source_id):
            if mapping.external_id not in seen_paths and mapping.status != "missing":
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
        for file in files:
            mapping = get_mapping(source_id=source_id, external_id=str(file.path), external_sub_id=None)
            meta = {}
            if mapping and mapping.meta_json:
                try:
                    meta = json.loads(mapping.meta_json)
                except json.JSONDecodeError:
                    meta = {}
            if mapping and meta.get("sha256") == file.sha256:
                skipped += 1
                continue
            try:
                data = file.path.read_bytes()
                target_path = docs_dir / file.path.name
                if copy_mode:
                    result = ingest_pdf(
                        workspace_id=context.workspace_id,
                        filename=target_path.name,
                        data=data,
                        save_dir=docs_dir,
                        ocr_mode=ocr_mode,
                        ocr_threshold=ocr_threshold,
                    )
                else:
                    if not target_path.exists():
                        target_path.symlink_to(file.path)
                    result = ingest_pdf(
                        workspace_id=context.workspace_id,
                        filename=target_path.name,
                        data=data,
                        save_dir=docs_dir,
                        write_file=False,
                        existing_path=target_path,
                        ocr_mode=ocr_mode,
                        ocr_threshold=ocr_threshold,
                    )
                set_document_source(
                    doc_id=result.doc_id,
                    source_type="folder",
                    source_ref=str(file.path),
                )
                upsert_mapping(
                    source_id=source_id,
                    external_id=str(file.path),
                    external_sub_id=None,
                    doc_id=result.doc_id,
                    status="ok",
                    meta={"sha256": file.sha256},
                )
                imported += 1
            except IngestError:
                upsert_mapping(
                    source_id=source_id,
                    external_id=str(file.path),
                    external_sub_id=None,
                    doc_id=None,
                    status="error",
                    meta={"sha256": file.sha256},
                )
                continue
        touch_source(source_id)
        return PluginResult(
            ok=True,
            message=f"Imported {imported} PDFs. Skipped {skipped}.",
            data={"imported": imported, "skipped": skipped},
        )
