from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

from core.ingest.ocr import OCRSettings, ocr_available, run_ocr
from core.ingest.pdf_render import render_page_image


class PDFReadError(RuntimeError):
    pass


@dataclass
class PDFPage:
    number: int
    text: str
    text_source: str
    ocr_text: str | None = None
    image_count: int = 0
    has_images: bool = False
    blocks_json: str | None = None


@dataclass
class PDFParseResult:
    pages: list[PDFPage]
    warnings: list[str] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)


def read_pdf(
    path: Path,
    *,
    ocr_mode: str = "off",
    ocr_threshold: int = 50,
    ocr_settings: OCRSettings | None = None,
    progress_cb: callable | None = None,
    stop_check: callable | None = None,
) -> PDFParseResult:
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
    warnings: list[str] = []
    ocr_settings = ocr_settings or OCRSettings()
    ocr_ready, ocr_reason = ocr_available(ocr_settings)
    if ocr_mode != "off" and not ocr_ready:
        warnings.append(
            f"OCR unavailable: {ocr_reason}. Proceeding with extracted text only."
        )
    try:
        for page_index in range(document.page_count):
            if stop_check and stop_check():
                raise PDFReadError("Ingest stopped by user.")
            page = document.load_page(page_index)
            text = page.get_text().strip()
            image_list = page.get_images(full=True)
            image_count = len(image_list)
            has_images = image_count > 0

            blocks = page.get_text("blocks")
            blocks_payload = [
                {
                    "x0": float(block[0]),
                    "y0": float(block[1]),
                    "x1": float(block[2]),
                    "y1": float(block[3]),
                    "text": str(block[4]).strip(),
                }
                for block in blocks
                if len(block) >= 5
            ]

            text_source = "extract"
            ocr_text = None
            extracted_text = text
            should_ocr = ocr_mode == "on" or (
                ocr_mode == "auto" and len(text) < ocr_threshold
            )
            if should_ocr and ocr_ready:
                image = render_page_image(page)
                ocr_text = run_ocr(image, settings=ocr_settings)
                if ocr_text:
                    text = f"{text}\n\n{ocr_text}".strip() if text else ocr_text
                    text_source = "ocr" if not extracted_text else "mixed"
                else:
                    text_source = text_source
            pages.append(
                PDFPage(
                    number=page_index + 1,
                    text=text,
                    text_source=text_source,
                    ocr_text=ocr_text,
                    image_count=image_count,
                    has_images=has_images,
                    blocks_json=json.dumps(blocks_payload, ensure_ascii=False)
                    if blocks_payload
                    else None,
                )
            )
            if progress_cb:
                progress_cb(page_index + 1, document.page_count)
    finally:
        document.close()

    if not pages:
        raise PDFReadError("PDF has no pages.")

    return PDFParseResult(pages=pages, warnings=warnings)
