from core.ingest.chunker import chunk_pages
from core.ingest.pdf_reader import PDFPage


def test_chunker_basic():
    pages = [
        PDFPage(number=1, text="Para one.\n\nPara two.", text_source="extract"),
        PDFPage(number=2, text="Para three.\n\nPara four.", text_source="extract"),
    ]
    chunks = chunk_pages(pages)
    assert chunks
    assert chunks[0].page_start >= 1
