from __future__ import annotations

GLOBAL_HINTS = {
    "全课",
    "整堂课",
    "考试",
    "exam",
    "blueprint",
    "overview",
    "总结",
    "course-wide",
    "whole course",
    "全项目",
    "related work",
    "literature review",
    "project-wide",
    "entire project",
    "deck",
    "汇报",
}


def classify_query(query: str) -> str:
    normalized = query.strip().lower()
    for hint in GLOBAL_HINTS:
        if hint in normalized:
            return "global"
    if len(normalized.split()) > 14:
        return "global"
    return "local"
