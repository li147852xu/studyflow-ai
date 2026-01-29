from __future__ import annotations

from core.concepts.store import list_evidence, search_cards
from service.document_service import get_document


def search_with_evidence(
    *, workspace_id: str, query: str, type_filter: str | None = None
) -> list[dict]:
    cards = search_cards(workspace_id=workspace_id, query=query, type_filter=type_filter)
    results: list[dict] = []
    for card in cards:
        evidences = list_evidence(card.id)
        rendered = []
        for evidence in evidences:
            doc = get_document(evidence.doc_id)
            filename = doc.get("filename") if doc else "unknown"
            page = evidence.page_start or "-"
            snippet = evidence.snippet or ""
            rendered.append(f"{filename} (p.{page}) {snippet}")
        results.append(
            {
                "card": card,
                "evidence": rendered,
            }
        )
    return results
