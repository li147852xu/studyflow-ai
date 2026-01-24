from __future__ import annotations

from pathlib import Path

import os
import time

from core.agents.slides_agent import SlidesAgent, SlidesOutput
from core.telemetry.run_logger import log_run
from infra.db import get_workspaces_dir
from service.paper_service import list_papers
from service.document_service import list_documents
from service.asset_service import create_asset_version, slides_ref_id
from core.quality.citations_check import check_citations
from service.metadata_service import llm_metadata


def list_sources(workspace_id: str) -> list[dict]:
    sources = []
    for doc in list_documents(workspace_id):
        sources.append(
            {
                "label": f"Document: {doc['filename']}",
                "doc_id": doc["id"],
                "type": "document",
            }
        )
    for paper in list_papers(workspace_id):
        sources.append(
            {
                "label": f"Paper: {paper['title']}",
                "doc_id": paper["doc_id"],
                "type": "paper",
            }
        )
    return sources


def generate_slides(
    *,
    workspace_id: str,
    doc_id: str,
    duration: str,
    retrieval_mode: str = "vector",
    save_outputs: bool = True,
) -> SlidesOutput:
    output_dir = None
    if save_outputs:
        output_dir = get_workspaces_dir() / workspace_id / "outputs"
    start = time.time()
    agent = SlidesAgent(workspace_id, doc_id, retrieval_mode)
    output = agent.generate(duration, output_dir=output_dir)
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.deck, output.hits or [])
    if citation_error:
        if output.warnings:
            output.warnings.append(citation_error)
        else:
            output.warnings = [citation_error]
    errors = citation_error
    if output.warnings:
        errors = "; ".join(output.warnings)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="slides",
        input_payload={"doc_id": doc_id, "duration": duration},
        retrieval_mode=output.retrieval_mode or retrieval_mode,
        hits=output.hits or [],
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=errors,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="slides",
        ref_id=slides_ref_id(doc_id, duration),
        content=output.deck,
        content_type="markdown",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode or retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v1",
        hits=output.hits or [],
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output
