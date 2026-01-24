from __future__ import annotations

from infra.db import get_connection
from core.retrieval.vector_store import VectorStore, VectorStoreSettings
from infra.db import get_workspaces_dir


def delete_document(workspace_id: str, doc_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        connection.execute("DELETE FROM document_pages WHERE doc_id = ?", (doc_id,))
        connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        connection.commit()


def delete_document_vectors(workspace_id: str, doc_id: str) -> None:
    settings = VectorStoreSettings(
        persist_directory=get_workspaces_dir() / workspace_id / "index" / "chroma",
        collection_name=f"workspace_{workspace_id}",
    )
    store = VectorStore(settings)
    store.collection.delete(where={"doc_id": doc_id})
