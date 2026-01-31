from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Citation:
    title: str
    location_label: str
    snippet: str

    def render(self) -> str:
        return f"{self.title} ({self.location_label})\n{self.snippet}"


def build_citation(
    *,
    filename: str,
    page_start: int,
    page_end: int,
    text: str,
    file_type: str | None = None,
    max_chars: int = 300,
) -> Citation:
    title = filename
    file_type = (file_type or "pdf").lower()
    if page_end != page_start:
        range_label = f"{page_start}-{page_end}"
    else:
        range_label = f"{page_start}"
    if file_type == "pdf":
        location_label = f"p.{range_label}"
    elif file_type == "docx":
        location_label = f"para {range_label}" if page_end == page_start else f"paras {range_label}"
    elif file_type == "pptx":
        location_label = f"slide {range_label}" if page_end == page_start else f"slides {range_label}"
    elif file_type in ["txt", "md"]:
        location_label = f"line {range_label}" if page_end == page_start else f"lines {range_label}"
    elif file_type in ["html", "htm"]:
        location_label = (
            f"element {range_label}" if page_end == page_start else f"elements {range_label}"
        )
    elif file_type in ["png", "jpg", "jpeg"]:
        location_label = f"image {range_label}"
    else:
        location_label = f"loc {range_label}"

    snippet = text.strip().replace("\n", " ")
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rstrip() + "..."
    if not snippet:
        snippet = "(no text)"

    return Citation(title=title, location_label=location_label, snippet=snippet)
