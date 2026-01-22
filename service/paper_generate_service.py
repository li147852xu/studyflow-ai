from __future__ import annotations

import os
import time

from core.agents.paper_agent import PaperAgent, PaperCardOutput
from core.agents.paper_aggregator import AggregationOutput, PaperAggregator
from core.telemetry.run_logger import log_run


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
    return output
