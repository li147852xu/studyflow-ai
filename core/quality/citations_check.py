from __future__ import annotations

import re

from core.ingest.cite import build_citation
from core.retrieval.retriever import Hit


def check_citations(content: str, hits: list[Hit]) -> tuple[bool, str | None]:
    if not content:
        return False, "Empty content."
    if not hits:
        return False, "No retrieval hits available for citations."
    matches = re.findall(r"\[(\d+)\]", content)
    if not matches:
        return False, "No citation markers found in output."
    used = {int(match) for match in matches if match.isdigit()}
    if not used:
        return False, "Invalid citation markers."
    max_index = len(hits)
    for idx in used:
        if idx < 1 or idx > max_index:
            return False, f"Citation index {idx} is out of range."
        hit = hits[idx - 1]
        if not hit.chunk_id or not hit.doc_id:
            return False, f"Citation {idx} is missing chunk metadata."
        if hit.page_start is None or hit.page_end is None or not hit.text:
            return False, f"Citation {idx} is missing page/text data."
        citation = build_citation(
            filename=hit.filename,
            page_start=hit.page_start,
            page_end=hit.page_end,
            text=hit.text,
            file_type=hit.file_type,
        )
        if not citation.snippet:
            return False, f"Citation {idx} snippet could not be built."
    return True, None
