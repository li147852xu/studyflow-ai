from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

from core.coach.coach_agent import CoachAgent, CoachOutput
from core.coach.store import (
    CoachSession,
    clear_sessions,
    create_session,
    get_session,
    list_sessions,
    update_phase_a,
    update_phase_b,
    write_session_file,
)
from core.telemetry.run_logger import log_run
from core.quality.citations_check import check_citations
from service.metadata_service import llm_metadata


def _hits_to_json(hits) -> str | None:
    if not hits:
        return None
    payload = [
        {
            "chunk_id": hit.chunk_id,
            "filename": hit.filename,
            "page_start": hit.page_start,
            "page_end": hit.page_end,
            "text": hit.text,
            "score": hit.score,
        }
        for hit in hits
    ]
    return json.dumps(payload, ensure_ascii=False)


@dataclass
class CoachSessionOutput:
    session: CoachSession
    output: CoachOutput


def start_coach(
    *, workspace_id: str, problem: str, retrieval_mode: str = "vector"
) -> CoachSessionOutput:
    session = create_session(workspace_id, problem)
    agent = CoachAgent(workspace_id, retrieval_mode=retrieval_mode)
    start = time.time()
    output = agent.phase_a(problem)
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="coach_phase_a",
        input_payload={"problem": problem, "prompt_version": output.prompt_version},
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
    update_phase_a(
        session.id,
        output.content,
        json.dumps(output.citations, ensure_ascii=False),
        _hits_to_json(output.hits),
    )
    write_session_file(get_session(session.id))
    return CoachSessionOutput(session=get_session(session.id), output=output)


def submit_coach(
    *,
    workspace_id: str,
    session_id: str,
    answer: str,
    retrieval_mode: str = "vector",
) -> CoachSessionOutput:
    session = get_session(session_id)
    agent = CoachAgent(workspace_id, retrieval_mode=retrieval_mode)
    start = time.time()
    output = agent.phase_b(session.problem, answer)
    latency_ms = int((time.time() - start) * 1000)
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="coach_phase_b",
        input_payload={"session_id": session_id, "prompt_version": output.prompt_version},
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
    update_phase_b(
        session.id,
        output.content,
        json.dumps(output.citations, ensure_ascii=False),
        _hits_to_json(output.hits),
    )
    write_session_file(get_session(session.id))
    return CoachSessionOutput(session=get_session(session.id), output=output)


def list_coach_sessions(workspace_id: str) -> list[CoachSession]:
    return list_sessions(workspace_id)


def show_coach_session(session_id: str) -> CoachSession:
    return get_session(session_id)


def clear_coach_sessions(workspace_id: str) -> None:
    clear_sessions(workspace_id)
