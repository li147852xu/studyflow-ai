from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache

from sentence_transformers import SentenceTransformer


class EmbeddingError(RuntimeError):
    pass


@dataclass
class EmbeddingSettings:
    model: str
    cache_dir: str | None = None
    batch_size: int = 32
    workers: int = 1
    max_retries: int = 2
    retry_base: float = 0.5


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

    batch_size = int(os.getenv("STUDYFLOW_EMBED_BATCH_SIZE", "32"))
    workers = int(os.getenv("STUDYFLOW_EMBED_WORKERS", "1"))
    max_retries = int(os.getenv("STUDYFLOW_EMBED_MAX_RETRIES", "2"))
    retry_base = float(os.getenv("STUDYFLOW_EMBED_RETRY_BASE", "0.5"))
    return EmbeddingSettings(
        model=resolved_model,
        cache_dir=cache_dir,
        batch_size=max(batch_size, 1),
        workers=max(workers, 1),
        max_retries=max(max_retries, 0),
        retry_base=max(retry_base, 0.1),
    )


@lru_cache(maxsize=2)
def _load_model(model_name: str, cache_dir: str | None) -> SentenceTransformer:
    try:
        return SentenceTransformer(model_name, cache_folder=cache_dir)
    except Exception as exc:
        raise EmbeddingError(f"Failed to load embeddings model: {exc}") from exc


def _encode_batch(texts: list[str], settings: EmbeddingSettings) -> list[list[float]]:
    cache_dir = getattr(settings, "cache_dir", None)
    model = _load_model(settings.model, cache_dir)
    for attempt in range(settings.max_retries + 1):
        try:
            embeddings = model.encode(
                texts,
                show_progress_bar=False,
                normalize_embeddings=True,
                batch_size=settings.batch_size,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as exc:
            if attempt >= settings.max_retries:
                raise EmbeddingError(f"Embedding failed after retries: {exc}") from exc
            time.sleep(settings.retry_base * (2**attempt))
    return []


def embed_texts(
    texts: list[str],
    settings: EmbeddingSettings,
) -> list[list[float]]:
    if not texts:
        return []
    batch_size = settings.batch_size
    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
    if settings.workers <= 1 or len(batches) == 1:
        results: list[list[list[float]]] = []
        for batch in batches:
            results.append(_encode_batch(batch, settings))
        return [item for batch in results for item in batch]
    embeddings: list[list[float]] = []
    with ThreadPoolExecutor(max_workers=settings.workers) as executor:
        for batch in executor.map(lambda b: _encode_batch(b, settings), batches):
            embeddings.extend(batch)
    return embeddings
