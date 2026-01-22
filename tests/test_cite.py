from core.ingest.cite import build_citation


def test_citation_format():
    citation = build_citation(
        filename="doc.pdf",
        page_start=2,
        page_end=3,
        text="Some text for citation.",
    )
    rendered = citation.render()
    assert "doc.pdf" in rendered
    assert "p.2-3" in rendered
