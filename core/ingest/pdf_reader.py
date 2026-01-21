from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


class PDFReadError(RuntimeError):
    pass


@dataclass
class PDFPage:
    number: int
    text: str


@dataclass
class PDFParseResult:
    pages: list[PDFPage]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def read_pdf(path: Path) -> PDFParseResult:
    if not path.exists():
        raise PDFReadError("PDF file not found.")
    if path.stat().st_size == 0:
        raise PDFReadError("PDF file is empty.")
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise PDFReadError("Failed to open PDF. The file may be corrupted.") from exc

    if document.is_encrypted:
        document.close()
        raise PDFReadError("PDF is encrypted. Please provide an unencrypted file.")

    pages: list[PDFPage] = []
    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            text = page.get_text().strip()
            pages.append(PDFPage(number=page_index + 1, text=text))
    finally:
        document.close()

    if not pages:
        raise PDFReadError("PDF has no pages.")

    return PDFParseResult(pages=pages)
