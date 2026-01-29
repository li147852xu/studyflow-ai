from __future__ import annotations

from infra.db import get_connection
from service.chat_service import ChatConfigError, chat
from service.document_service import get_document, set_document_summary


class SummaryError(RuntimeError):
    pass


def _get_document_chunks(doc_id: str, limit: int = 5) -> list[str]:
    """Get the first N chunks of a document."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT text FROM chunks
            WHERE doc_id = ?
            ORDER BY chunk_index ASC
            LIMIT ?
            """,
            (doc_id, limit),
        ).fetchall()
    return [row["text"] for row in rows]


def generate_summary(doc_id: str) -> str:
    """Generate a one-line summary for a document using LLM."""
    doc = get_document(doc_id)
    if not doc:
        raise SummaryError("Document not found.")

    chunks = _get_document_chunks(doc_id, limit=5)
    if not chunks:
        raise SummaryError("No chunks found for document. Please ensure document is ingested.")

    context = "\n\n".join(chunks[:5])
    if len(context) > 4000:
        context = context[:4000] + "..."

    prompt = (
        "Based on the following document excerpt, generate a single concise sentence (max 100 characters) "
        "summarizing what this document is about. Output ONLY the summary sentence, nothing else.\n\n"
        f"Document: {doc['filename']}\n\n"
        f"Content:\n{context}"
    )

    try:
        summary = chat(prompt=prompt, temperature=0.3)
        summary = summary.strip().strip('"').strip("'")
        if len(summary) > 150:
            summary = summary[:147] + "..."
        set_document_summary(doc_id=doc_id, summary=summary)
        return summary
    except ChatConfigError as exc:
        raise SummaryError(f"LLM error: {exc}") from exc
