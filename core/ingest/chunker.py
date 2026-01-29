from __future__ import annotations

import json
from dataclasses import dataclass

from core.ingest.pdf_reader import PDFPage

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


@dataclass
class Chunk:
    chunk_index: int
    page_start: int
    page_end: int
    text: str
    text_source: str
    metadata_json: str | None = None


def _split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in text.split("\n\n")]
    return [p for p in parts if p]


def _hard_split(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]


def chunk_pages(pages: list[PDFPage]) -> list[Chunk]:
    paragraphs: list[tuple[int, str]] = []
    page_meta: dict[int, PDFPage] = {page.number: page for page in pages}
    for page in pages:
        if not page.text:
            continue
        for para in _split_paragraphs(page.text):
            paragraphs.append((page.number, para))

    chunks: list[Chunk] = []
    current_text = ""
    page_start = None
    page_end = None
    chunk_index = 0
    carry_text = ""
    carry_page = None

    def flush_chunk() -> None:
        nonlocal current_text, page_start, page_end, chunk_index, carry_text, carry_page
        if not current_text:
            return
        sources = set()
        ocr_pages: list[int] = []
        image_pages: list[int] = []
        if page_start and page_end:
            for page_num in range(page_start, page_end + 1):
                meta = page_meta.get(page_num)
                if not meta:
                    continue
                sources.add(meta.text_source)
                if meta.text_source in ["ocr", "mixed"]:
                    ocr_pages.append(page_num)
                if meta.has_images:
                    image_pages.append(page_num)
        text_source = "mixed" if len(sources) > 1 else (next(iter(sources)) if sources else "extract")
        metadata_json = json.dumps(
            {
                "ocr_pages": ocr_pages,
                "image_pages": image_pages,
            },
            ensure_ascii=False,
        )
        chunks.append(
            Chunk(
                chunk_index=chunk_index,
                page_start=page_start or page_end or 1,
                page_end=page_end or page_start or 1,
                text=current_text.strip(),
                text_source=text_source,
                metadata_json=metadata_json,
            )
        )
        chunk_index += 1
        if CHUNK_OVERLAP > 0:
            carry_text = current_text[-CHUNK_OVERLAP:].strip()
            carry_page = page_end or page_start
        else:
            carry_text = ""
            carry_page = None
        current_text = ""
        page_start = None
        page_end = None

    def start_with_carry() -> None:
        nonlocal current_text, page_start, page_end, carry_text, carry_page
        if carry_text:
            current_text = carry_text
            page_start = carry_page
            page_end = carry_page
            carry_text = ""
            carry_page = None

    for page_num, para in paragraphs:
        if not current_text:
            start_with_carry()

        candidate = f"{current_text}\n\n{para}".strip() if current_text else para
        if len(candidate) <= CHUNK_SIZE:
            current_text = candidate
            page_start = page_start or page_num
            page_end = page_num
            continue

        if current_text:
            flush_chunk()
            start_with_carry()
            candidate = f"{current_text}\n\n{para}".strip() if current_text else para

        if len(candidate) <= CHUNK_SIZE:
            current_text = candidate
            page_start = page_start or page_num
            page_end = page_num
            continue

        # Hard split for very long paragraph
        for segment in _hard_split(para, CHUNK_SIZE):
            if current_text:
                flush_chunk()
                start_with_carry()
            current_text = segment
            page_start = page_start or page_num
            page_end = page_num
            flush_chunk()

    if current_text:
        flush_chunk()

    return chunks
