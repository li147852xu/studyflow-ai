from __future__ import annotations

import os
import time

from core.agents.paper_agent import PaperAgent, PaperCardOutput
from core.agents.paper_aggregator import AggregationOutput, PaperAggregator
from core.telemetry.run_logger import log_run
from service.asset_service import create_asset_version, paper_aggregate_ref_id, paper_ref_id
from core.quality.citations_check import check_citations
from service.metadata_service import llm_metadata
from service.document_service import filter_doc_ids_by_type, get_document


def generate_paper_card(
    *,
    workspace_id: str,
    doc_id: str,
    retrieval_mode: str = "vector",
    progress_cb: callable | None = None,
) -> PaperCardOutput:
    doc = get_document(doc_id)
    if not doc or doc.get("doc_type") != "paper":
        raise RuntimeError("Paper outputs require a doc_type of 'paper'.")
    start = time.time()
    agent = PaperAgent(workspace_id, doc_id, retrieval_mode)
    output = agent.generate_paper_card(progress_cb=progress_cb)
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
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
        action_type="paper_card",
        input_payload={"doc_id": doc_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
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
        kind="paper_card",
        ref_id=paper_ref_id(doc_id),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
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
    filtered_doc_ids = filter_doc_ids_by_type(doc_ids, "paper")
    if not filtered_doc_ids:
        raise RuntimeError("Paper aggregation requires paper documents.")
    start = time.time()
    aggregator = PaperAggregator(workspace_id, filtered_doc_ids, retrieval_mode)
    output = aggregator.aggregate(question, progress_cb=progress_cb)
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    if citation_error:
        output.warnings = [citation_error]
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="paper_aggregate",
        input_payload={"doc_ids": filtered_doc_ids, "question": question},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )
    output.run_id = run_id
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="paper_aggregate",
        ref_id=paper_aggregate_ref_id(filtered_doc_ids, question),
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v1",
        hits=output.hits,
    )
    output.asset_id = version.asset_id
    output.asset_version_id = version.id
    output.asset_version_index = version.version_index
    return output
