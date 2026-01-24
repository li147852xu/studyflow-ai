from __future__ import annotations

import os


def llm_metadata(
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    seed: int | None = None,
) -> dict:
    provider = os.getenv("STUDYFLOW_LLM_PROVIDER", "openai_compat")
    model = os.getenv("STUDYFLOW_LLM_MODEL", "")
    embed_model = os.getenv("STUDYFLOW_EMBED_MODEL", "")
    temp = (
        temperature
        if temperature is not None
        else float(os.getenv("STUDYFLOW_LLM_TEMPERATURE", "0.2"))
    )
    max_toks = (
        max_tokens
        if max_tokens is not None
        else int(os.getenv("STUDYFLOW_LLM_MAX_TOKENS", "0") or "0")
    )
    seed_val = (
        seed
        if seed is not None
        else int(os.getenv("STUDYFLOW_LLM_SEED", "0") or "0")
    )
    return {
        "provider": provider,
        "model": model,
        "embed_model": embed_model,
        "temperature": temp if temp != 0 else None if temperature is None else temp,
        "max_tokens": max_toks or None,
        "seed": seed_val or None,
    }
