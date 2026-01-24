from __future__ import annotations

import json
import os
import time
from pathlib import Path

from core.related.manager import build_related, update_related, RelatedManagerError
from core.related.store import (
    create_project,
    update_project,
    replace_sections,
    add_candidates,
    list_sections,
    get_project,
)
from core.telemetry.run_logger import log_run
from service.asset_service import create_asset_version
from service.paper_service import list_papers
from infra.db import get_workspaces_dir
from core.quality.citations_check import check_citations
from service.metadata_service import llm_metadata


class RelatedServiceError(RuntimeError):
    pass


def _resolve_doc_ids(workspace_id: str, paper_ids: list[str]) -> list[str]:
    papers = [paper for paper in list_papers(workspace_id) if paper["id"] in paper_ids]
    return [paper["doc_id"] for paper in papers]


def create_related_project(
    *,
    workspace_id: str,
    paper_ids: list[str],
    topic: str,
    retrieval_mode: str,
) -> dict:
    doc_ids = _resolve_doc_ids(workspace_id, paper_ids)
    if not doc_ids:
        raise RelatedServiceError("No papers selected for related project.")
    start = time.time()
    result = build_related(
        workspace_id=workspace_id,
        doc_ids=doc_ids,
        topic=topic,
        retrieval_mode=retrieval_mode,
    )
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(result.draft, result.hits)
    warnings = getattr(result, "warnings", None)
    errors = citation_error
    if warnings:
        errors = "; ".join(warnings + ([citation_error] if citation_error else []))
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="related_create",
        input_payload={"topic": topic, "prompt_version": result.prompt_version},
        retrieval_mode=result.retrieval_mode,
        hits=result.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=result.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=errors,
    )
    project_id = create_project(
        workspace_id=workspace_id,
        topic=topic,
        comparison_axes=result.comparison_axes,
        draft=result.draft,
    )
    section_ids = replace_sections(project_id=project_id, sections=result.sections)
    for section_id in section_ids:
        add_candidates(project_id=project_id, section_id=section_id, paper_ids=paper_ids)
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="related_work",
        ref_id=project_id,
        content=result.draft,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=result.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=result.prompt_version or "v1",
        hits=result.hits,
    )
    return {
        "project_id": project_id,
        "draft": result.draft,
        "citations": result.citations,
        "warnings": warnings or ([] if citation_ok else [citation_error or "citation check failed"]),
        "asset_version_id": version.id,
        "run_id": run_id,
    }


def update_related_project(
    *,
    workspace_id: str,
    project_id: str,
    add_paper_ids: list[str],
    retrieval_mode: str,
) -> dict:
    project = get_project(project_id)
    if not project:
        raise RelatedServiceError("Related project not found.")
    doc_ids = _resolve_doc_ids(workspace_id, add_paper_ids)
    if not doc_ids:
        raise RelatedServiceError("No new papers selected for update.")
    outline = "\n".join([f"- {section.title}" for section in list_sections(project_id)])
    start = time.time()
    result = update_related(
        workspace_id=workspace_id,
        doc_ids=doc_ids,
        topic=project.topic,
        existing_outline=outline,
        retrieval_mode=retrieval_mode,
    )
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(result.draft, result.hits)
    warnings = getattr(result, "warnings", None)
    errors = citation_error
    if warnings:
        errors = "; ".join(warnings + ([citation_error] if citation_error else []))
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="related_update",
        input_payload={"project_id": project_id, "prompt_version": result.prompt_version},
        retrieval_mode=result.retrieval_mode,
        hits=result.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=result.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=errors,
    )
    update_project(
        project_id=project_id,
        comparison_axes=result.comparison_axes,
        draft=result.draft,
    )
    section_ids = replace_sections(project_id=project_id, sections=result.sections)
    for section_id in section_ids:
        add_candidates(project_id=project_id, section_id=section_id, paper_ids=add_paper_ids)
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="related_work",
        ref_id=project_id,
        content=result.draft,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=result.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=result.prompt_version or "v1",
        hits=result.hits,
    )
    return {
        "project_id": project_id,
        "draft": result.draft,
        "citations": result.citations,
        "insert_suggestions": result.insert_suggestions or [],
        "warnings": warnings or ([] if citation_ok else [citation_error or "citation check failed"]),
        "asset_version_id": version.id,
        "run_id": run_id,
    }


def export_related_project(
    *,
    workspace_id: str,
    project_id: str,
    format: str,
    out_path: str | None = None,
) -> str:
    project = get_project(project_id)
    if not project:
        raise RelatedServiceError("Related project not found.")
    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "related"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = Path(out_path) if out_path else output_dir / f"related_{project_id}.{format}"
    if format == "json":
        payload = {
            "project_id": project.id,
            "topic": project.topic,
            "comparison_axes": json.loads(project.comparison_axes_json or "[]"),
            "draft": project.current_draft or "",
            "sections": [section.__dict__ for section in list_sections(project_id)],
        }
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(target)
    if format == "txt":
        content = project.current_draft or ""
        target.write_text(content, encoding="utf-8")
        return str(target)
    raise RelatedServiceError("Format must be json or txt.")
