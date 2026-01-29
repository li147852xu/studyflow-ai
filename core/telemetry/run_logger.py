from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from core.retrieval.retriever import Hit
from infra.db import get_workspaces_dir


@dataclass
class RunLog:
    run_id: str
    timestamp: str
    workspace_id: str
    action_type: str
    input: dict
    retrieval_mode: str
    retrieval_hits: list[dict]
    model: str
    provider: str
    temperature: float | None
    max_tokens: int | None
    embed_model: str
    seed: int | None
    prompt_version: str | None
    latency_ms: int
    citation_incomplete: bool | None = None
    errors: str | None = None


def _run_dir(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "runs"


def _now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log_run(
    *,
    workspace_id: str,
    action_type: str,
    input_payload: dict,
    retrieval_mode: str,
    hits: list[Hit],
    model: str,
    provider: str,
    temperature: float | None,
    max_tokens: int | None,
    embed_model: str,
    seed: int | None,
    prompt_version: str | None,
    latency_ms: int,
    citation_incomplete: bool | None = None,
    errors: str | None = None,
) -> str:
    run_id = str(uuid.uuid4())
    payload = RunLog(
        run_id=run_id,
        timestamp=_now_ts(),
        workspace_id=workspace_id,
        action_type=action_type,
        input=input_payload,
        retrieval_mode=retrieval_mode,
        retrieval_hits=[
            {
                "chunk_id": hit.chunk_id,
                "doc_id": hit.doc_id,
                "page_start": hit.page_start,
                "page_end": hit.page_end,
                "score": hit.score,
            }
            for hit in hits
        ],
        model=model,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
        embed_model=embed_model,
        seed=seed,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
        citation_incomplete=citation_incomplete,
        errors=errors,
    )
    try:
        run_dir = _run_dir(workspace_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / f"run_{run_id}.json"
        path.write_text(json.dumps(payload.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # Logging failures must not break main flow
        return run_id
    return run_id
