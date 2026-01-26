from __future__ import annotations

from core.external.downloader import download_arxiv, DownloadError
from core.external.sources import create_source, find_source, touch_source, upsert_mapping
from core.plugins.base import PluginBase, PluginContext, PluginResult
from infra.db import get_workspaces_dir
from service.document_service import set_document_source
from service.ingest_service import ingest_pdf, IngestError


class ImportArxivPlugin(PluginBase):
    name = "importer_arxiv"
    version = "1.0.0"
    description = "Download and ingest an arXiv PDF."

    def run(self, context: PluginContext) -> PluginResult:
        arxiv_id = context.args.get("arxiv_id")
        if not arxiv_id:
            return PluginResult(ok=False, message="Missing arXiv id.")
        ocr_mode = context.args.get("ocr_mode", "off")
        ocr_threshold = int(context.args.get("ocr_threshold", 50))
        doc_type = context.args.get("doc_type", "paper")

        source = find_source(
            workspace_id=context.workspace_id,
            source_type="arxiv",
            params={"id": arxiv_id},
        )
        source_id = source.id if source else create_source(
            workspace_id=context.workspace_id,
            source_type="arxiv",
            params={"id": arxiv_id},
        )
        try:
            data, filename = download_arxiv(arxiv_id)
            docs_dir = get_workspaces_dir() / context.workspace_id / "docs"
            result = ingest_pdf(
                workspace_id=context.workspace_id,
                filename=filename,
                data=data,
                save_dir=docs_dir,
                ocr_mode=ocr_mode,
                ocr_threshold=ocr_threshold,
                doc_type=doc_type,
            )
            set_document_source(
                doc_id=result.doc_id,
                source_type="arxiv",
                source_ref=arxiv_id,
            )
            upsert_mapping(
                source_id=source_id,
                external_id=arxiv_id,
                external_sub_id=None,
                doc_id=result.doc_id,
                status="ok",
            )
            touch_source(source_id)
            return PluginResult(ok=True, message=f"Imported arXiv {arxiv_id}.")
        except (DownloadError, IngestError) as exc:
            upsert_mapping(
                source_id=source_id,
                external_id=arxiv_id,
                external_sub_id=None,
                doc_id=None,
                status="error",
                meta={"error": str(exc)},
            )
            return PluginResult(ok=False, message=str(exc))
