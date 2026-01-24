from __future__ import annotations

FORBIDDEN_PHRASES = [
    "final answer",
    "full solution",
    "complete solution",
    "entire solution",
    "give me the answer",
    "直接答案",
    "最终答案",
    "完整答案",
    "完整解答",
    "给出答案",
    "给出完整解答",
]


def requires_guard(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in FORBIDDEN_PHRASES)
