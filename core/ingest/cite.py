from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Citation:
    title: str
    page_label: str
    snippet: str

    def render(self) -> str:
        return f"{self.title} ({self.page_label})\n{self.snippet}"


def build_citation(
    *,
    filename: str,
    page_start: int,
    page_end: int,
    text: str,
    max_chars: int = 300,
) -> Citation:
    title = filename
    if page_end != page_start:
        page_label = f"p.{page_start}-{page_end}"
    else:
        page_label = f"p.{page_start}"

    snippet = text.strip().replace("\n", " ")
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rstrip() + "..."
    if not snippet:
        snippet = "(no text)"

    return Citation(title=title, page_label=page_label, snippet=snippet)
