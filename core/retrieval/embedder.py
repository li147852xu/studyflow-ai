from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import SentenceTransformer


class EmbeddingError(RuntimeError):
    pass


@dataclass
class EmbeddingSettings:
    model: str


def build_embedding_settings(
    *,
    model: str | None = None,
) -> EmbeddingSettings:
    resolved_model = (
        model
        if model is not None
        else os.getenv("STUDYFLOW_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    resolved_model = resolved_model.strip()

    if not resolved_model:
        raise EmbeddingError(
            "Missing embeddings model. Set STUDYFLOW_EMBED_MODEL."
        )

    return EmbeddingSettings(
        model=resolved_model,
    )


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> SentenceTransformer:
    try:
        return SentenceTransformer(model_name)
    except Exception as exc:
        raise EmbeddingError(f"Failed to load embeddings model: {exc}") from exc


def embed_texts(
    texts: list[str],
    settings: EmbeddingSettings,
) -> list[list[float]]:
    if not texts:
        return []
    model = _load_model(settings.model)
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]
