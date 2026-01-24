from __future__ import annotations

from pathlib import Path

from core.plugins.base import PluginBase, PluginContext, PluginResult
from service.ingest_service import ingest_pdf, IngestError
from infra.db import get_workspaces_dir


class ImportFolderPlugin(PluginBase):
    name = "importer_folder"
    version = "1.0.0"
    description = "Import all PDFs from a folder into the workspace."

    def run(self, context: PluginContext) -> PluginResult:
        folder = context.args.get("path")
        if not folder:
            return PluginResult(ok=False, message="Missing path.")
        ocr_mode = context.args.get("ocr_mode", "off")
        ocr_threshold = int(context.args.get("ocr_threshold", 50))
        path = Path(folder)
        if not path.exists():
            return PluginResult(ok=False, message="Folder not found.")
        pdfs = list(path.glob("*.pdf"))
        if not pdfs:
            return PluginResult(ok=True, message="No PDF files found.", data={"count": 0})
        count = 0
        for pdf in pdfs:
            try:
                ingest_pdf(
                    workspace_id=context.workspace_id,
                    filename=pdf.name,
                    data=pdf.read_bytes(),
                    save_dir=get_workspaces_dir() / context.workspace_id / "uploads",
                    ocr_mode=ocr_mode,
                    ocr_threshold=ocr_threshold,
                )
                count += 1
            except IngestError:
                continue
        return PluginResult(ok=True, message=f"Imported {count} PDFs.", data={"count": count})
