from __future__ import annotations

from typing import List

from pydantic import BaseModel, ValidationError, validator


class PaperCardSchema(BaseModel):
    summary: str
    contributions: List[str]
    strengths: List[str]
    weaknesses: List[str]
    extensions: List[str]

    @validator("summary")
    def _summary_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary must not be empty")
        return value


class SlideSchema(BaseModel):
    title: str
    bullets: List[str]
    notes: List[str]

    @validator("title")
    def _title_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value


class SlidesPlanSchema(BaseModel):
    slides: List[SlideSchema]

    @validator("slides")
    def _slides_not_empty(cls, value: list) -> list:
        if len(value) < 2:
            raise ValueError("slides must include at least 2 slides")
        return value


class RelatedSectionSchema(BaseModel):
    title: str
    bullets: List[str]


class RelatedOutlineSchema(BaseModel):
    comparison_axes: List[str]
    sections: List[RelatedSectionSchema]
    draft: str


def parse_paper_card(content: str) -> PaperCardSchema:
    sections = {
        "summary": "",
        "contributions": [],
        "strengths": [],
        "weaknesses": [],
        "extensions": [],
    }
    current = None
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        header = stripped.lower().rstrip(":")
        if header in sections:
            current = header
            continue
        if current in ("contributions", "strengths", "weaknesses", "extensions"):
            if stripped.startswith("-"):
                sections[current].append(stripped.lstrip("- ").strip())
            else:
                sections[current].append(stripped)
        elif current == "summary":
            sections["summary"] += (stripped + " ")
    return PaperCardSchema(
        summary=sections["summary"].strip(),
        contributions=sections["contributions"],
        strengths=sections["strengths"],
        weaknesses=sections["weaknesses"],
        extensions=sections["extensions"],
    )


def parse_slides_deck(deck: str) -> SlidesPlanSchema:
    slides = []
    parts = [part.strip() for part in deck.split("\n---\n") if part.strip()]
    for part in parts:
        lines = [line.strip() for line in part.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0].startswith("---"):
            lines = lines[1:]
        title = ""
        bullets = []
        notes = []
        in_notes = False
        for line in lines:
            if line.lower().startswith("notes:"):
                in_notes = True
                continue
            if not title:
                title = line
                continue
            if line.startswith("-"):
                item = line.lstrip("- ").strip()
                if in_notes:
                    notes.append(item)
                else:
                    bullets.append(item)
        slides.append(SlideSchema(title=title, bullets=bullets, notes=notes))
    return SlidesPlanSchema(slides=slides)


def validate_related_payload(payload: dict) -> RelatedOutlineSchema:
    return RelatedOutlineSchema(**payload)


def validate_paper_card(content: str) -> tuple[bool, str | None]:
    try:
        parse_paper_card(content)
        return True, None
    except ValidationError as exc:
        return False, str(exc)


def validate_slides_deck(deck: str) -> tuple[bool, str | None]:
    try:
        parse_slides_deck(deck)
        return True, None
    except ValidationError as exc:
        return False, str(exc)


def validate_related_payload_safe(payload: dict) -> tuple[bool, str | None]:
    try:
        validate_related_payload(payload)
        return True, None
    except ValidationError as exc:
        return False, str(exc)
