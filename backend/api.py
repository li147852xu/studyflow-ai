from __future__ import annotations

import base64
import os

from fastapi import Depends, FastAPI, Header, HTTPException

from backend.schemas import (
    AssetVersionResponse,
    AssetVersionsResponse,
    CoachResponse,
    CoachStartRequest,
    CoachSubmitRequest,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ImportRequest,
    ImportResponse,
    IngestRequest,
    IngestResponse,
    OcrStatusResponse,
    PluginsResponse,
    PromptsResponse,
    QueryRequest,
    QueryResponse,
    WorkspaceRequest,
    WorkspaceResponse,
)
from core.assets.citations import format_citations_payload
from core.assets.store import get_asset
from core.ingest.ocr import OCRSettings, ocr_available
from core.plugins.registry import load_builtin_plugins, list_plugins, get_plugin
from core.plugins.base import PluginContext
from core.prompts.registry import list_prompts
from infra.db import get_connection, get_workspaces_dir
from infra.models import init_db
from service.asset_service import list_versions, read_version
from service.coach_service import start_coach, submit_coach
from service.course_service import generate_cheatsheet, generate_overview, explain_selection
from service.ingest_service import ingest_pdf
from service.paper_generate_service import aggregate_papers, generate_paper_card
from service.paper_service import ingest_paper, get_paper
from service.document_service import get_document
from service.presentation_service import generate_slides
from service.retrieval_service import answer_with_retrieval
from service.workspace_service import create_workspace, list_workspaces

app = FastAPI(title="StudyFlow API", version="2.4.0")


def _verify_token(authorization: str | None = Header(None)) -> None:
    token = os.getenv("API_TOKEN", "")
    if not token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API token.")
    provided = authorization.replace("Bearer ", "").strip()
    if provided != token:
        raise HTTPException(status_code=403, detail="Invalid API token.")


@app.on_event("startup")
def _init_db() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="2.4.0")


@app.get("/ocr/status", response_model=OcrStatusResponse, dependencies=[Depends(_verify_token)])
def ocr_status() -> OcrStatusResponse:
    ok, reason = ocr_available(OCRSettings())
    return OcrStatusResponse(
        available=ok,
        engine="auto",
        message=reason or "OCR available",
    )


@app.post("/workspaces", response_model=WorkspaceResponse, dependencies=[Depends(_verify_token)])
def workspaces(payload: WorkspaceRequest) -> WorkspaceResponse:
    if payload.action == "create":
        if not payload.name:
            raise HTTPException(status_code=400, detail="Workspace name required.")
        create_workspace(payload.name)
    return WorkspaceResponse(workspaces=list_workspaces())


@app.post("/ingest", response_model=IngestResponse, dependencies=[Depends(_verify_token)])
def ingest(payload: IngestRequest) -> IngestResponse:
    try:
        data = base64.b64decode(payload.data_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 payload.") from exc
    if payload.kind == "paper":
        paper_id, metadata = ingest_paper(
            workspace_id=payload.workspace_id,
            filename=payload.filename,
            data=data,
            save_dir=get_workspaces_dir() / payload.workspace_id / "uploads",
            ocr_mode=payload.ocr_mode,
            ocr_threshold=payload.ocr_threshold,
        )
        paper = get_paper(paper_id)
        doc_id = paper["doc_id"] if paper else ""
        doc = get_document(doc_id) if doc_id else None
        chunk_count = 0
        if doc_id:
            with get_connection() as connection:
                row = connection.execute(
                    "SELECT COUNT(*) as count FROM chunks WHERE doc_id = ?",
                    (doc_id,),
                ).fetchone()
                chunk_count = int(row["count"]) if row else 0
        return IngestResponse(
            doc_id=doc_id,
            workspace_id=payload.workspace_id,
            filename=doc["filename"] if doc else payload.filename,
            path=doc["path"] if doc else "",
            sha256=doc.get("sha256") if doc else "",
            page_count=int(doc.get("page_count") or 0) if doc else 0,
            chunk_count=chunk_count,
            skipped=False,
            paper_id=paper_id,
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
        )
    result = ingest_pdf(
        workspace_id=payload.workspace_id,
        filename=payload.filename,
        data=data,
        save_dir=get_workspaces_dir() / payload.workspace_id / "uploads",
        ocr_mode=payload.ocr_mode,
        ocr_threshold=payload.ocr_threshold,
    )
    return IngestResponse(**result.__dict__)


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(_verify_token)])
def query(payload: QueryRequest) -> QueryResponse:
    answer, hits, citations, run_id = answer_with_retrieval(
        workspace_id=payload.workspace_id,
        query=payload.query,
        mode=payload.mode,
        top_k=payload.top_k,
    )
    return QueryResponse(
        answer=answer,
        hits=[hit.__dict__ for hit in hits],
        citations=citations,
        run_id=run_id,
    )


@app.post("/generate", response_model=GenerateResponse, dependencies=[Depends(_verify_token)])
def generate(payload: GenerateRequest) -> GenerateResponse:
    if payload.action_type == "course_overview":
        output = generate_overview(
            workspace_id=payload.workspace_id,
            course_id=payload.course_id or "",
            retrieval_mode=payload.retrieval_mode or "vector",
        )
        return GenerateResponse(
            content=output.content,
            citations=output.citations,
            run_id=output.run_id,
            asset_id=output.asset_id,
            asset_version_id=output.asset_version_id,
            asset_version_index=output.asset_version_index,
        )
    if payload.action_type == "course_cheatsheet":
        output = generate_cheatsheet(
            workspace_id=payload.workspace_id,
            course_id=payload.course_id or "",
            retrieval_mode=payload.retrieval_mode or "vector",
        )
        return GenerateResponse(
            content=output.content,
            citations=output.citations,
            run_id=output.run_id,
            asset_id=output.asset_id,
            asset_version_id=output.asset_version_id,
            asset_version_index=output.asset_version_index,
        )
    if payload.action_type == "course_explain":
        output = explain_selection(
            workspace_id=payload.workspace_id,
            course_id=payload.course_id or "",
            selection=payload.selection or "",
            mode=payload.mode or "plain",
            retrieval_mode=payload.retrieval_mode or "vector",
        )
        return GenerateResponse(
            content=output.content,
            citations=output.citations,
            run_id=output.run_id,
            asset_id=output.asset_id,
            asset_version_id=output.asset_version_id,
            asset_version_index=output.asset_version_index,
        )
    if payload.action_type == "paper_card":
        output = generate_paper_card(
            workspace_id=payload.workspace_id,
            doc_id=payload.doc_id or "",
            retrieval_mode=payload.retrieval_mode or "vector",
        )
        return GenerateResponse(
            content=output.content,
            citations=output.citations,
            run_id=output.run_id,
            asset_id=output.asset_id,
            asset_version_id=output.asset_version_id,
            asset_version_index=output.asset_version_index,
        )
    if payload.action_type == "paper_aggregate":
        output = aggregate_papers(
            workspace_id=payload.workspace_id,
            doc_ids=payload.doc_ids or [],
            question=payload.question or "",
            retrieval_mode=payload.retrieval_mode or "vector",
        )
        return GenerateResponse(
            content=output.content,
            citations=output.citations,
            run_id=output.run_id,
            asset_id=output.asset_id,
            asset_version_id=output.asset_version_id,
            asset_version_index=output.asset_version_index,
        )
    if payload.action_type == "slides":
        output = generate_slides(
            workspace_id=payload.workspace_id,
            doc_id=payload.doc_id or "",
            duration=payload.duration or "10",
            retrieval_mode=payload.retrieval_mode or "vector",
        )
        return GenerateResponse(
            deck=output.deck,
            qa=output.qa,
            citations=output.citations,
            run_id=output.run_id,
            asset_id=output.asset_id,
            asset_version_id=output.asset_version_id,
            asset_version_index=output.asset_version_index,
        )
    raise HTTPException(status_code=400, detail="Unknown action_type.")


@app.get(
    "/assets/{asset_id}/versions",
    response_model=AssetVersionsResponse,
    dependencies=[Depends(_verify_token)],
)
def asset_versions(asset_id: str) -> AssetVersionsResponse:
    asset = get_asset(asset_id)
    versions = list_versions(asset_id)
    return AssetVersionsResponse(
        asset_id=asset.id,
        versions=[
            {
                "id": version.id,
                "version_index": version.version_index,
                "run_id": version.run_id,
                "model": version.model,
                "prompt_version": version.prompt_version,
                "created_at": version.created_at,
            }
            for version in versions
        ],
    )


@app.get(
    "/assets/{asset_id}/version/{version_id}",
    response_model=AssetVersionResponse,
    dependencies=[Depends(_verify_token)],
)
def asset_version(asset_id: str, version_id: str) -> AssetVersionResponse:
    view = read_version(asset_id, version_id)
    citations = []
    if view.version.hits_json:
        citations = format_citations_payload(view.version.hits_json)
    return AssetVersionResponse(
        asset_id=asset_id,
        version_id=version_id,
        content=view.content,
        content_type=view.version.content_type,
        citations=citations,
    )


@app.post(
    "/coach/start",
    response_model=CoachResponse,
    dependencies=[Depends(_verify_token)],
)
def coach_start(payload: CoachStartRequest) -> CoachResponse:
    result = start_coach(
        workspace_id=payload.workspace_id,
        problem=payload.problem,
        retrieval_mode=payload.retrieval_mode,
    )
    return CoachResponse(
        session_id=result.session.id,
        content=result.output.content,
        citations=result.output.citations,
        run_id=result.output.run_id,
    )


@app.post(
    "/coach/submit",
    response_model=CoachResponse,
    dependencies=[Depends(_verify_token)],
)
def coach_submit(payload: CoachSubmitRequest) -> CoachResponse:
    result = submit_coach(
        workspace_id=payload.workspace_id,
        session_id=payload.session_id,
        answer=payload.answer,
        retrieval_mode=payload.retrieval_mode,
    )
    return CoachResponse(
        session_id=result.session.id,
        content=result.output.content,
        citations=result.output.citations,
        run_id=result.output.run_id,
    )


@app.get(
    "/plugins",
    response_model=PluginsResponse,
    dependencies=[Depends(_verify_token)],
)
def plugins_list() -> PluginsResponse:
    load_builtin_plugins()
    return PluginsResponse(
        plugins=[
            {"name": plugin.name, "version": plugin.version, "description": plugin.description}
            for plugin in list_plugins()
        ]
    )


@app.get(
    "/prompts",
    response_model=PromptsResponse,
    dependencies=[Depends(_verify_token)],
)
def prompts_list() -> PromptsResponse:
    return PromptsResponse(
        prompts=[
            {"name": prompt.name, "version": prompt.version}
            for prompt in list_prompts()
        ]
    )


def _run_import(name: str, payload: ImportRequest) -> ImportResponse:
    load_builtin_plugins()
    plugin = get_plugin(name)
    result = plugin.run(
        PluginContext(
            workspace_id=payload.workspace_id,
            args=payload.params,
        )
    )
    return ImportResponse(ok=result.ok, message=result.message, data=result.data)


@app.post(
    "/import/zotero",
    response_model=ImportResponse,
    dependencies=[Depends(_verify_token)],
)
def import_zotero(payload: ImportRequest) -> ImportResponse:
    return _run_import("importer_zotero", payload)


@app.post(
    "/import/arxiv",
    response_model=ImportResponse,
    dependencies=[Depends(_verify_token)],
)
def import_arxiv(payload: ImportRequest) -> ImportResponse:
    return _run_import("importer_arxiv", payload)


@app.post(
    "/import/doi",
    response_model=ImportResponse,
    dependencies=[Depends(_verify_token)],
)
def import_doi(payload: ImportRequest) -> ImportResponse:
    return _run_import("importer_doi", payload)


@app.post(
    "/import/url",
    response_model=ImportResponse,
    dependencies=[Depends(_verify_token)],
)
def import_url(payload: ImportRequest) -> ImportResponse:
    return _run_import("importer_url", payload)


@app.post(
    "/import/folder",
    response_model=ImportResponse,
    dependencies=[Depends(_verify_token)],
)
def import_folder(payload: ImportRequest) -> ImportResponse:
    return _run_import("importer_folder_sync", payload)
