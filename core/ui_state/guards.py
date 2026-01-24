from __future__ import annotations


def llm_ready(base_url: str, model: str, api_key: str) -> tuple[bool, str]:
    if not base_url.strip():
        return False, "Missing LLM base URL. Set it in Settings or config."
    if not model.strip():
        return False, "Missing LLM model. Set it in Settings or config."
    if not api_key.strip():
        return False, "Missing LLM API key. Set it in env or Settings."
    return True, ""
