from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from core.ingest.ocr import OCRSettings, ocr_available, run_ocr


def test_ocr_pipeline_optional(tmp_path: Path):
    settings = OCRSettings()
    ok, reason = ocr_available(settings)
    if not ok:
        pytest.skip(f"OCR unavailable: {reason}")

    image = Image.new("RGB", (200, 60), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "OCR TEST", fill="black")

    text = run_ocr(image, settings=settings)
    assert isinstance(text, str)
