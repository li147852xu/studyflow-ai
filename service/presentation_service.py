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
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="slides",
        input_payload={"doc_id": doc_id, "duration": duration},
        retrieval_mode=output.retrieval_mode or retrieval_mode,
        hits=output.hits or [],
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
        latency_ms=latency_ms,
        errors=None,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="slides",
        ref_id=slides_ref_id(doc_id, duration),
        content=output.deck,
        content_type="markdown",
        run_id=run_id,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        prompt_version="v1",
        hits=output.hits or [],
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output
