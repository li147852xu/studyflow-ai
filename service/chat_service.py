from __future__ import annotations

import os

from core.llm.client import LLMClient, LLMClientError, LLMSettings


class ChatConfigError(ValueError):
    pass


def build_settings(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> LLMSettings:
    resolved_base_url = (
        base_url
        if base_url is not None
        else os.getenv("STUDYFLOW_LLM_BASE_URL", "")
    )
    resolved_api_key = (
        api_key
        if api_key is not None
        else os.getenv("STUDYFLOW_LLM_API_KEY", "")
    )
    resolved_model = (
        model
        if model is not None
        else os.getenv("STUDYFLOW_LLM_MODEL", "")
    )

    resolved_base_url = resolved_base_url.strip()
    resolved_api_key = resolved_api_key.strip()
    resolved_model = resolved_model.strip()

    if not resolved_base_url:
        raise ChatConfigError("Missing LLM base URL. Set STUDYFLOW_LLM_BASE_URL.")
    if not resolved_model:
        raise ChatConfigError("Missing LLM model. Set STUDYFLOW_LLM_MODEL.")
    if not resolved_api_key:
        raise ChatConfigError("Missing API key. Set STUDYFLOW_LLM_API_KEY.")

    return LLMSettings(
        base_url=resolved_base_url,
        api_key=resolved_api_key,
        model=resolved_model,
    )


def chat(
    *,
    prompt: str,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    settings = build_settings(base_url=base_url, api_key=api_key, model=model)
    client = LLMClient(settings)
    messages = [
        {"role": "system", "content": "You are a helpful study assistant."},
        {"role": "user", "content": prompt},
    ]
    return client.chat(messages)
