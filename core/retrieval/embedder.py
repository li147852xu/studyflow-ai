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
    cache_dir: str | None = None


def build_embedding_settings(
    *,
    model: str | None = None,
) -> EmbeddingSettings:
    resolved_model = (
        model
        if model is not None
        else os.getenv("STUDYFLOW_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    cache_dir = os.getenv("STUDYFLOW_EMBED_CACHE_DIR", "").strip() or None
    resolved_model = resolved_model.strip()

    if not resolved_model:
        raise EmbeddingError(
            "Missing embeddings model. Set STUDYFLOW_EMBED_MODEL."
        )

    return EmbeddingSettings(model=resolved_model, cache_dir=cache_dir)


@lru_cache(maxsize=2)
def _load_model(model_name: str, cache_dir: str | None) -> SentenceTransformer:
    try:
        return SentenceTransformer(model_name, cache_folder=cache_dir)
    except Exception as exc:
        raise EmbeddingError(f"Failed to load embeddings model: {exc}") from exc


def embed_texts(
    texts: list[str],
    settings: EmbeddingSettings,
) -> list[list[float]]:
    if not texts:
        return []
    cache_dir = getattr(settings, "cache_dir", None)
    model = _load_model(settings.model, cache_dir)
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]
