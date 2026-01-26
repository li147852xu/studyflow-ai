from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from infra.db import get_workspaces_dir
from core.ui_state.storage import get_setting
from core.prompts.course_prompts import cheatsheet_prompt, explain_prompt, overview_prompt
from core.prompts.paper_prompts import aggregator_prompt, paper_card_prompt
from core.prompts.slides_prompts import qa_prompt, slides_prompt
from core.prompts.coach_prompts import coach_phase_a_prompt, coach_phase_b_prompt
from core.prompts.concepts_prompts import concept_cards_prompt
from core.prompts.related_prompts import related_create_prompt, related_update_prompt


@dataclass
class PromptSpec:
    name: str
    version: str
    builder: callable


_PROMPTS: dict[str, PromptSpec] = {
    "course_overview": PromptSpec("course_overview", "v1", overview_prompt),
    "course_cheatsheet": PromptSpec("course_cheatsheet", "v1", cheatsheet_prompt),
    "course_explain": PromptSpec("course_explain", "v1", explain_prompt),
    "paper_card": PromptSpec("paper_card", "v1", paper_card_prompt),
    "paper_aggregate": PromptSpec("paper_aggregate", "v1", aggregator_prompt),
    "slides": PromptSpec("slides", "v1", slides_prompt),
    "slides_qa": PromptSpec("slides_qa", "v1", qa_prompt),
    "coach_phase_a": PromptSpec("coach_phase_a", "v1", coach_phase_a_prompt),
    "coach_phase_b": PromptSpec("coach_phase_b", "v1", coach_phase_b_prompt),
    "concept_cards": PromptSpec("concept_cards", "v1", concept_cards_prompt),
    "related_create": PromptSpec("related_create", "v1", related_create_prompt),
    "related_update": PromptSpec("related_update", "v1", related_update_prompt),
}


def list_prompts() -> list[PromptSpec]:
    return list(_PROMPTS.values())


def _override_path(workspace_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "prompts_override.json"


def load_override(workspace_id: str) -> dict:
    path = _override_path(workspace_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _selected_version(workspace_id: str | None, default_version: str) -> str:
    if not workspace_id:
        return default_version
    stored = get_setting(workspace_id, "prompt_version") or get_setting(None, "prompt_version")
    return stored or default_version


def build_prompt(name: str, workspace_id: str | None, **kwargs) -> tuple[str, str]:
    spec = _PROMPTS.get(name)
    if not spec:
        raise RuntimeError("Unknown prompt name.")
    version = _selected_version(workspace_id, spec.version)
    if "language" not in kwargs:
        language = None
        if workspace_id:
            language = get_setting(workspace_id, "output_language")
        language = language or get_setting(None, "output_language") or "en"
        kwargs["language"] = language
    if workspace_id:
        override = load_override(workspace_id)
        override_text = (
            override.get("prompts", {})
            .get(name, {})
            .get(version)
        )
        if isinstance(override_text, str):
            return override_text.format(**kwargs), version
    return spec.builder(**kwargs), version
