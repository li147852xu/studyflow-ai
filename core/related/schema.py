from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RelatedProject:
    id: str
    workspace_id: str
    topic: str
    comparison_axes_json: str | None
    current_draft: str | None
    created_at: str
    updated_at: str


@dataclass
class RelatedSection:
    id: str
    project_id: str
    section_index: int
    title: str
    bullets_json: str | None
    created_at: str
    updated_at: str
