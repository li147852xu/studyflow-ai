from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb


@dataclass
class VectorStoreSettings:
    persist_directory: Path
    collection_name: str


class VectorStore:
    def __init__(self, settings: VectorStoreSettings) -> None:
        self.settings = settings
        self.settings.persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.settings.persist_directory)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name
        )

    def count(self) -> int:
        return self.collection.count()

    def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self.collection.upsert(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def query(
        self,
        *,
        embedding: list[float],
        top_k: int,
        where: dict | None = None,
    ) -> dict:
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
            where=where,
        )

    def reset(self) -> None:
        self.client.delete_collection(name=self.settings.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name
        )
