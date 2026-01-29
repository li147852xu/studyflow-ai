from __future__ import annotations

from pydantic import BaseModel, ValidationError, validator


class PaperCardSchema(BaseModel):
    summary: str
    contributions: list[str]
    strengths: list[str]
    weaknesses: list[str]
    extensions: list[str]

    @validator("summary")
    def _summary_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary must not be empty")
        return value


class SlideSchema(BaseModel):
    title: str
    bullets: list[str]
    notes: list[str]

    @validator("title")
    def _title_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be empty")
        return value


class SlidesPlanSchema(BaseModel):
    slides: list[SlideSchema]

    @validator("slides")
    def _slides_not_empty(cls, value: list) -> list:
        if len(value) < 2:
            raise ValueError("slides must include at least 2 slides")
        return value


class RelatedSectionSchema(BaseModel):
    title: str
    bullets: list[str]


class RelatedOutlineSchema(BaseModel):
    comparison_axes: list[str]
    sections: list[RelatedSectionSchema]
    draft: str


def parse_paper_card(content: str) -> PaperCardSchema:
    sections = {
        "summary": "",
        "contributions": [],
        "strengths": [],
        "weaknesses": [],
        "extensions": [],
    }
    # Map various header variations to canonical names
    header_map = {
        "summary": "summary",
        "abstract": "summary",
        "overview": "summary",
        "contributions": "contributions",
        "key contributions": "contributions",
        "contribution": "contributions",
        "strengths": "strengths",
        "strength": "strengths",
        "pros": "strengths",
        "weaknesses": "weaknesses",
        "weakness": "weaknesses",
        "limitations": "weaknesses",
        "cons": "weaknesses",
        "extensions": "extensions",
        "extension ideas": "extensions",
        "future work": "extensions",
        "extension": "extensions",
    }
    current = None
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Check for header (with or without colon, with optional markdown #)
        header = stripped.lstrip("#").strip().lower().rstrip(":")
        if header in header_map:
            current = header_map[header]
            continue
        if current in ("contributions", "strengths", "weaknesses", "extensions"):
            # Handle bullet points with various markers
            if stripped.startswith(("-", "*", "•", "·")):
                item = stripped.lstrip("-*•· ").strip()
                if item and item.lower() not in ("tbd", "n/a", "none"):
                    sections[current].append(item)
            elif stripped[0].isdigit() and ("." in stripped[:3] or ")" in stripped[:3]):
                # Handle numbered lists like "1. item" or "1) item"
                item = stripped.split(".", 1)[-1].split(")", 1)[-1].strip()
                if item and item.lower() not in ("tbd", "n/a", "none"):
                    sections[current].append(item)
            elif current and stripped:
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
