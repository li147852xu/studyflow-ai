from __future__ import annotations

import os
from dataclasses import dataclass

import requests


class EmbeddingError(RuntimeError):
    pass


@dataclass
class EmbeddingSettings:
    base_url: str
    api_key: str
    model: str


def build_embedding_settings(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> EmbeddingSettings:
    resolved_base_url = (
        base_url
        if base_url is not None
        else os.getenv("STUDYFLOW_EMBED_BASE_URL")
        or os.getenv("STUDYFLOW_LLM_BASE_URL", "")
    )
    resolved_api_key = (
        api_key
        if api_key is not None
        else os.getenv("STUDYFLOW_EMBED_API_KEY")
        or os.getenv("STUDYFLOW_LLM_API_KEY", "")
    )
    resolved_model = (
        model
        if model is not None
        else os.getenv("STUDYFLOW_EMBED_MODEL", "")
    )

    resolved_base_url = resolved_base_url.strip()
    resolved_api_key = resolved_api_key.strip()
    resolved_model = resolved_model.strip()

    if not resolved_base_url:
        raise EmbeddingError(
            "Missing embeddings base URL. Set STUDYFLOW_EMBED_BASE_URL."
        )
    if not resolved_model:
        raise EmbeddingError(
            "Missing embeddings model. Set STUDYFLOW_EMBED_MODEL."
        )
    if not resolved_api_key:
        raise EmbeddingError(
            "Missing embeddings API key. Set STUDYFLOW_EMBED_API_KEY."
        )

    return EmbeddingSettings(
        base_url=resolved_base_url,
        api_key=resolved_api_key,
        model=resolved_model,
    )


def embed_texts(
    texts: list[str],
    settings: EmbeddingSettings,
    timeout: int = 60,
) -> list[list[float]]:
    if not texts:
        return []
    url = settings.base_url.rstrip("/") + "/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.model, "input": texts}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise EmbeddingError(f"Embeddings request failed: {exc}") from exc

    data = response.json()
    try:
        embeddings = [item["embedding"] for item in data["data"]]
    except (KeyError, TypeError) as exc:
        raise EmbeddingError("Unexpected embeddings response format.") from exc

    if len(embeddings) != len(texts):
        raise EmbeddingError("Embeddings count mismatch.")

    return embeddings
