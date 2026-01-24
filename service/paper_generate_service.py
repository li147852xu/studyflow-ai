from __future__ import annotations

import os
import time

from core.agents.paper_agent import PaperAgent, PaperCardOutput
from core.agents.paper_aggregator import AggregationOutput, PaperAggregator
from core.telemetry.run_logger import log_run
from service.asset_service import create_asset_version, paper_aggregate_ref_id, paper_ref_id


def generate_paper_card(
    *,
    workspace_id: str,
    doc_id: str,
    retrieval_mode: str = "vector",
    progress_cb: callable | None = None,
) -> PaperCardOutput:
    start = time.time()
    agent = PaperAgent(workspace_id, doc_id, retrieval_mode)
    output = agent.generate_paper_card(progress_cb=progress_cb)
    latency_ms = int((time.time() - start) * 1000)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="paper_card",
        input_payload={"doc_id": doc_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
        latency_ms=latency_ms,
        errors=None,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="paper_card",
        ref_id=paper_ref_id(doc_id),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        prompt_version=output.prompt_version or "v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output


def aggregate_papers(
    *,
    workspace_id: str,
    doc_ids: list[str],
    question: str,
    retrieval_mode: str = "vector",
    progress_cb: callable | None = None,
) -> AggregationOutput:
    start = time.time()
    aggregator = PaperAggregator(workspace_id, doc_ids, retrieval_mode)
    output = aggregator.aggregate(question, progress_cb=progress_cb)
    latency_ms = int((time.time() - start) * 1000)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="paper_aggregate",
        input_payload={"doc_ids": doc_ids, "question": question},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        embed_model=os.getenv("STUDYFLOW_EMBED_MODEL", ""),
        latency_ms=latency_ms,
        errors=None,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="paper_aggregate",
        ref_id=paper_aggregate_ref_id(doc_ids, question),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=os.getenv("STUDYFLOW_LLM_MODEL", ""),
        prompt_version=output.prompt_version or "v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output
