from __future__ import annotations

import difflib


def diff_text(a: str, b: str, context: int = 3) -> str:
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    diff = difflib.unified_diff(
        a_lines,
        b_lines,
        fromfile="version_a",
        tofile="version_b",
        lineterm="",
        n=context,
    )
    return "\n".join(diff)
