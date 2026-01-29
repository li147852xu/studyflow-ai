from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image


@dataclass
class OCRSettings:
    language: str = "eng"
    engine: str = "auto"  # auto | pytesseract | easyocr


def _pytesseract_available() -> tuple[bool, str]:
    try:
        import pytesseract

        try:
            _ = pytesseract.get_tesseract_version()
        except Exception as exc:  # pragma: no cover
            return False, f"tesseract not found ({exc})"
        return True, ""
    except Exception as exc:  # pragma: no cover
        return False, f"pytesseract not installed ({exc})"


def _easyocr_available() -> tuple[bool, str]:
    try:
        import easyocr  # noqa: F401
        return True, ""
    except Exception as exc:  # pragma: no cover
        return False, f"easyocr not installed ({exc})"


def ocr_available(settings: OCRSettings | None = None) -> tuple[bool, str]:
    settings = settings or OCRSettings()
    if settings.engine == "pytesseract":
        return _pytesseract_available()
    if settings.engine == "easyocr":
        return _easyocr_available()
    pt_ok, pt_reason = _pytesseract_available()
    if pt_ok:
        return True, ""
    eo_ok, eo_reason = _easyocr_available()
    if eo_ok:
        return True, ""
    return False, f"{pt_reason}; {eo_reason}"


_EASYOCR_READER: Any | None = None


def run_ocr(image: Image.Image, *, settings: OCRSettings | None = None) -> str:
    settings = settings or OCRSettings()
    if settings.engine in ["auto", "pytesseract"]:
        ok, _ = _pytesseract_available()
        if ok:
            import pytesseract
            try:
                return pytesseract.image_to_string(image, lang=settings.language).strip()
            except Exception:
                return ""
        if settings.engine == "pytesseract":
            return ""
    if settings.engine in ["auto", "easyocr"]:
        ok, _ = _easyocr_available()
        if ok:
            global _EASYOCR_READER
            if _EASYOCR_READER is None:
                import easyocr

                lang = settings.language
                if lang == "eng":
                    lang = "en"
                _EASYOCR_READER = easyocr.Reader([lang], gpu=False)
            image_np = np.array(image)
            results = _EASYOCR_READER.readtext(image_np)
            return "\n".join([item[1] for item in results]).strip()
    return ""
