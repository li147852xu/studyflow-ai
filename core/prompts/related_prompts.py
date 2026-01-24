from __future__ import annotations


def related_create_prompt(context: str, topic: str) -> str:
    return (
        "You are drafting a related work section using provided sources.\n"
        "Return JSON only with fields: comparison_axes (list of strings), "
        "sections (list of {title, bullets}), draft (string).\n"
        "Use citation indices like [1][2] in bullets and draft.\n"
        f"\nTopic:\n{topic}\n\nContext:\n{context}\n"
    )


def related_update_prompt(context: str, topic: str, existing_outline: str) -> str:
    return (
        "You are updating a related work outline and draft with new papers.\n"
        "Return JSON only with fields: insert_suggestions (list), sections (list of {title, bullets}), draft (string).\n"
        "Use citation indices like [1][2].\n"
        f"\nTopic:\n{topic}\n\nExisting outline:\n{existing_outline}\n\nContext:\n{context}\n"
    )
