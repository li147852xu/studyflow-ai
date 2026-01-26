from __future__ import annotations


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"
    value = language.strip().lower()
    if value in {"zh", "zh-cn", "zh-hans", "chinese", "cn"}:
        return "zh"
    if value in {"en", "en-us", "english"}:
        return "en"
    return "en"


def language_instruction(language: str) -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return "使用中文为主，保留必要英文术语。"
    return "Use English primarily and keep necessary technical terms."


def rag_balance_instruction(language: str) -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "允许使用通用知识补充回答，但必须明确区分：\n"
            "1) 有据内容：必须带引用编号 [n]\n"
            "2) 通用知识：不得带引用编号\n"
        )
    return (
        "You may use general knowledge to supplement the answer, but clearly separate:\n"
        "1) Grounded content: must include citation markers [n]\n"
        "2) General knowledge: must not include citation markers\n"
    )


def general_knowledge_label(language: str) -> str:
    return "通用知识补充" if normalize_language(language) == "zh" else "General knowledge supplement"


def grounded_label(language: str) -> str:
    return "有据内容" if normalize_language(language) == "zh" else "Grounded content"
