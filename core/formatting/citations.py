from __future__ import annotations

from dataclasses import dataclass

from core.retrieval.retriever import Hit
from core.ingest.cite import build_citation


@dataclass
class CitationBundle:
    numbered_context: str
    citations: list[str]


def build_citation_bundle(hits: list[Hit], max_chars: int = 3500) -> CitationBundle:
    numbered_parts: list[str] = []
    citations: list[str] = []
    total = 0
    for idx, hit in enumerate(hits, start=1):
        snippet = hit.text.strip().replace("\n", " ")
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        entry = f"[{idx}] {snippet}"
        if total + len(entry) > max_chars:
            break
        numbered_parts.append(entry)
        total += len(entry)

        citation = build_citation(
            filename=hit.filename,
            page_start=hit.page_start,
            page_end=hit.page_end,
            text=hit.text,
        )
        citations.append(f"[{idx}] {citation.render()}")

    return CitationBundle(numbered_context="\n".join(numbered_parts), citations=citations)
