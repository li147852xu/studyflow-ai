from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PaperMetadata:
    title: str
    authors: str
    year: str


def extract_metadata(text: str) -> PaperMetadata | None:
    if not text.strip():
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    # Heuristic: title is the first line with reasonable length
    title = ""
    for line in lines[:10]:
        if 5 <= len(line) <= 200 and not line.lower().startswith("arxiv"):
            title = line
            break
    if not title:
        return None

    # Heuristic: authors appear after title
    authors = ""
    title_index = lines.index(title)
    for line in lines[title_index + 1 : title_index + 6]:
        if len(line) <= 200 and not re.search(r"\b\d{4}\b", line):
            authors = line
            break
    if not authors:
        authors = "unknown"

    # Year extraction
    year_match = re.search(r"\b(19|20)\d{2}\b", text[:2000])
    year = year_match.group(0) if year_match else "unknown"

    return PaperMetadata(title=title, authors=authors, year=year)
