from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConceptCard:
    id: str
    workspace_id: str
    name: str
    type: str
    content: str
    created_at: str
    updated_at: str


@dataclass
class ConceptEvidence:
    id: str
    card_id: str
    doc_id: str
    chunk_id: str
    page_start: int | None
    page_end: int | None
    snippet: str | None
    created_at: str
