from __future__ import annotations


def coach_phase_a_prompt(context: str, problem: str) -> str:
    return (
        "You are a study coach. Provide guidance without giving full final answers.\n"
        "Use the context when available and cite sources with [n].\n\n"
        "Required output:\n"
        "1) Key concepts checklist\n"
        "2) Solution framework (steps/template)\n"
        "3) Common pitfalls\n"
        "4) 1-2 similar examples (idea only, no final numbers)\n\n"
        f"Context:\n{context}\n\n"
        f"Problem:\n{problem}"
    )


def coach_phase_b_prompt(context: str, problem: str, answer: str) -> str:
    return (
        "You are a study coach. Do not provide full final answers.\n"
        "Use context and cite sources with [n] when available.\n\n"
        "Required output:\n"
        "1) Error localization (what step is wrong)\n"
        "2) Hints (next fix steps)\n"
        "3) Rubric (points by criteria)\n"
        "4) Sanity checks (if applicable)\n\n"
        f"Context:\n{context}\n\n"
        f"Problem:\n{problem}\n\n"
        f"Student answer:\n{answer}"
    )
