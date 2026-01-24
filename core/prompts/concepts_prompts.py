from __future__ import annotations


def concept_cards_prompt(context: str) -> str:
    return (
        "You are extracting concept cards from study materials.\n"
        "Return JSON array only, no extra text.\n"
        "Each item schema:\n"
        "{\n"
        '  "name": "...",\n'
        '  "type": "definition|formula|method|assumption|limitation|metric",\n'
        '  "content": "structured bullets or short paragraphs",\n'
        '  "evidence": [1,2]\n'
        "}\n"
        "Use evidence indices from the provided context, and keep cards concise.\n"
        f"\nContext:\n{context}\n"
    )
