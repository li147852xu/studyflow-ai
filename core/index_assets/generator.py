from __future__ import annotations

import re
from dataclasses import dataclass

from infra.db import get_connection
from service.chat_service import ChatConfigError, chat


@dataclass
class IndexAssets:
    summary_text: str
    outline: dict
    entities: list[str]


def _fetch_document_text(doc_id: str, max_chars: int = 12000) -> str:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT text
            FROM chunks
            WHERE doc_id = ?
            ORDER BY chunk_index ASC
            """,
            (doc_id,),
        ).fetchall()
    parts: list[str] = []
    total = 0
    for row in rows:
        text = (row["text"] or "").strip()
        if not text:
            continue
        if total + len(text) > max_chars:
            text = text[: max_chars - total]
        parts.append(text)
        total += len(text)
        if total >= max_chars:
            break
    return "\n".join(parts)


def _fallback_assets(text: str) -> IndexAssets:
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    summary = " ".join(sentences[:8]).strip() or text[:1200]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    headings: list[dict] = []
    for line in lines:
        if re.match(r"^(#+\s+|[0-9]{1,2}\.\s+)", line):
            headings.append({"title": line.lstrip("#").strip(), "level": 1})
        if len(headings) >= 8:
            break
    if not headings:
        headings = [{"title": sentence[:120], "level": 1} for sentence in sentences[:6] if sentence]
    entities = list(
        dict.fromkeys(
            re.findall(r"\b[A-Z][A-Za-z0-9_-]{2,}\b", text)
            + re.findall(r"\b[A-Za-z]{2,}\d+\b", text)
        )
    )[:20]
    return IndexAssets(summary_text=summary, outline={"sections": headings}, entities=entities)


def _llm_assets(text: str) -> IndexAssets:
    prompt = (
        "You are building index assets for offline retrieval.\n"
        "Return JSON with keys: summary_text (300-800 tokens), outline (sections list), entities (list of key terms).\n"
        "Keep it concise and grounded in the input text.\n\n"
        f"Text:\n{text}\n"
    )
    response = chat(prompt=prompt, max_tokens=900, temperature=0.2)
    summary_match = re.search(r'"summary_text"\s*:\s*"([^"]+)"', response)
    outline_match = re.search(r'"outline"\s*:\s*(\{.*\})', response, re.DOTALL)
    entities_match = re.search(r'"entities"\s*:\s*\[([^\]]*)\]', response, re.DOTALL)
    summary_text = summary_match.group(1) if summary_match else response[:1200]
    outline = {"sections": []}
    if outline_match:
        outline = {"raw": outline_match.group(1)}
    entities: list[str] = []
    if entities_match:
        entities = [item.strip().strip('"') for item in entities_match.group(1).split(",") if item.strip()]
    return IndexAssets(summary_text=summary_text, outline=outline, entities=entities)


def generate_doc_index_assets(doc_id: str) -> IndexAssets:
    text = _fetch_document_text(doc_id)
    if not text:
        return IndexAssets(summary_text="", outline={"sections": []}, entities=[])
    try:
        return _llm_assets(text)
    except ChatConfigError:
        return _fallback_assets(text)
