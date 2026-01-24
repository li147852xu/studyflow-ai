from __future__ import annotations

from core.external.downloader import download_url, DownloadError
from core.external.sources import create_source, find_source, touch_source, upsert_mapping
from core.plugins.base import PluginBase, PluginContext, PluginResult
from infra.db import get_workspaces_dir
from service.document_service import set_document_source
from service.ingest_service import ingest_pdf, IngestError


class ImportUrlPlugin(PluginBase):
    name = "importer_url"
    version = "1.0.0"
    description = "Download and ingest a direct PDF URL."

    def run(self, context: PluginContext) -> PluginResult:
        url = context.args.get("url")
        if not url:
            return PluginResult(ok=False, message="Missing URL.")
        ocr_mode = context.args.get("ocr_mode", "off")
        ocr_threshold = int(context.args.get("ocr_threshold", 50))

        source = find_source(
            workspace_id=context.workspace_id,
            source_type="url",
            params={"url": url},
        )
        source_id = source.id if source else create_source(
            workspace_id=context.workspace_id,
            source_type="url",
            params={"url": url},
        )
        try:
            data, filename = download_url(url)
            docs_dir = get_workspaces_dir() / context.workspace_id / "docs"
            result = ingest_pdf(
                workspace_id=context.workspace_id,
                filename=filename,
                data=data,
                save_dir=docs_dir,
                ocr_mode=ocr_mode,
                ocr_threshold=ocr_threshold,
            )
            set_document_source(
                doc_id=result.doc_id,
                source_type="url",
                source_ref=url,
            )
            upsert_mapping(
                source_id=source_id,
                external_id=url,
                external_sub_id=None,
                doc_id=result.doc_id,
                status="ok",
            )
            touch_source(source_id)
            return PluginResult(ok=True, message="Imported URL PDF.")
        except (DownloadError, IngestError) as exc:
            upsert_mapping(
                source_id=source_id,
                external_id=url,
                external_sub_id=None,
                doc_id=None,
                status="error",
                meta={"error": str(exc)},
            )
            return PluginResult(ok=False, message=str(exc))
