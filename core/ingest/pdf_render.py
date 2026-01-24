from __future__ import annotations

import fitz  # PyMuPDF
from PIL import Image


def render_page_image(page: fitz.Page, zoom: float = 2.0) -> Image.Image:
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    mode = "RGB"
    return Image.frombytes(mode, [pix.width, pix.height], pix.samples)
