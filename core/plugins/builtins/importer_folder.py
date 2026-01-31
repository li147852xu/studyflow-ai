from __future__ import annotations

from pathlib import Path

from core.plugins.base import PluginBase, PluginContext, PluginResult
from infra.db import get_workspaces_dir
from service.ingest_service import IngestError, ingest_document


class ImportFolderPlugin(PluginBase):
    name = "importer_folder"
    version = "1.0.0"
    description = "Import supported files from a folder into the workspace."

    def run(self, context: PluginContext) -> PluginResult:
        folder = context.args.get("path")
        if not folder:
            return PluginResult(ok=False, message="Missing path.")
        ocr_mode = context.args.get("ocr_mode", "off")
        ocr_threshold = int(context.args.get("ocr_threshold", 50))
        doc_type = context.args.get("doc_type", "other")
        path = Path(folder)
        if not path.exists():
            return PluginResult(ok=False, message="Folder not found.")
        supported_exts = {
            ".pdf",
            ".txt",
            ".md",
            ".docx",
            ".pptx",
            ".html",
            ".htm",
            ".png",
            ".jpg",
            ".jpeg",
        }
        files = [entry for entry in path.iterdir() if entry.suffix.lower() in supported_exts]
        if not files:
            return PluginResult(
                ok=True, message="No supported files found.", data={"count": 0}
            )
        count = 0
        for doc_path in files:
            try:
                ingest_document(
                    workspace_id=context.workspace_id,
                    filename=doc_path.name,
                    data=doc_path.read_bytes(),
                    save_dir=get_workspaces_dir() / context.workspace_id / "uploads",
                    ocr_mode=ocr_mode,
                    ocr_threshold=ocr_threshold,
                    doc_type=doc_type,
                )
                count += 1
            except IngestError:
                continue
        return PluginResult(
            ok=True, message=f"Imported {count} files.", data={"count": count}
        )
