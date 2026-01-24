from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class WorkspaceRequest(BaseModel):
    action: str = "list"
    name: str | None = None


class WorkspaceResponse(BaseModel):
    workspaces: list[dict[str, Any]]


class IngestRequest(BaseModel):
    workspace_id: str
    filename: str
    data_base64: str
    kind: str = "document"
    ocr_mode: str = "off"
    ocr_threshold: int = 50


class IngestResponse(BaseModel):
    doc_id: str
    workspace_id: str
    filename: str
    path: str
    sha256: str
    page_count: int
    chunk_count: int
    skipped: bool
    ocr_pages_count: int | None = None
    image_pages_count: int | None = None
    ocr_mode: str | None = None
    warnings: list[str] | None = None
    paper_id: str | None = None
    title: str | None = None
    authors: str | None = None
    year: str | None = None


class QueryRequest(BaseModel):
    workspace_id: str
    query: str
    mode: str = "vector"
    top_k: int = 8


class QueryResponse(BaseModel):
    answer: str
    hits: list[dict[str, Any]]
    citations: list[str]
    run_id: str


class GenerateRequest(BaseModel):
    action_type: str
    workspace_id: str
    retrieval_mode: str | None = None
    course_id: str | None = None
    doc_id: str | None = None
    doc_ids: list[str] | None = None
    question: str | None = None
    selection: str | None = None
    mode: str | None = None
    duration: str | None = None


class GenerateResponse(BaseModel):
    content: str | None = None
    deck: str | None = None
    qa: list[str] | None = None
    citations: list[str]
    run_id: str | None
    asset_id: str | None
    asset_version_id: str | None
    asset_version_index: int | None


class AssetVersionsResponse(BaseModel):
    asset_id: str
    versions: list[dict[str, Any]]


class AssetVersionResponse(BaseModel):
    asset_id: str
    version_id: str
    content: str
    content_type: str
    citations: list[dict[str, Any]]


class OcrStatusResponse(BaseModel):
    available: bool
    engine: str
    message: str


class CoachStartRequest(BaseModel):
    workspace_id: str
    problem: str
    retrieval_mode: str = "vector"


class CoachSubmitRequest(BaseModel):
    workspace_id: str
    session_id: str
    answer: str
    retrieval_mode: str = "vector"


class CoachResponse(BaseModel):
    session_id: str
    content: str
    citations: list[str]
    run_id: str | None


class PluginsResponse(BaseModel):
    plugins: list[dict[str, Any]]


class PromptsResponse(BaseModel):
    prompts: list[dict[str, Any]]


class ImportRequest(BaseModel):
    workspace_id: str
    params: dict[str, Any]


class ImportResponse(BaseModel):
    ok: bool
    message: str
    data: dict[str, Any] | None = None


class BundleExportRequest(BaseModel):
    workspace_id: str
    with_pdf: bool = False
    with_assets: bool = False
    with_prompts: bool = False


class BundleExportResponse(BaseModel):
    path: str


class BundleImportRequest(BaseModel):
    path: str
    rebuild_index: bool = False


class BundleImportResponse(BaseModel):
    workspace_id: str


class PackRequest(BaseModel):
    workspace_id: str
    pack_type: str
    source_id: str


class PackResponse(BaseModel):
    path: str
