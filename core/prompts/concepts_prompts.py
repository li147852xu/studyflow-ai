from __future__ import annotations

from core.prompts.instructions import language_instruction, normalize_language


def concept_cards_prompt(context: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你正在从学习材料中提取概念卡片。\n"
            f"{language_instruction(lang)}\n"
            "仅返回 JSON 数组，不要输出额外文本。\n"
            "每项结构：\n"
            "{\n"
            '  "name": "...",\n'
            '  "type": "definition|formula|method|assumption|limitation|metric",\n'
            '  "content": "structured bullets or short paragraphs",\n'
            '  "evidence": [1,2]\n'
            "}\n"
            "content 字段使用中文撰写（保留必要英文术语），键名保持英文。\n"
            "使用上下文中的证据索引，保持简洁。\n"
            f"\n上下文：\n{context}\n"
        )
    return (
        "You are extracting concept cards from study materials.\n"
        f"{language_instruction(lang)}\n"
        "Return JSON array only, no extra text.\n"
        "Each item schema:\n"
        "{\n"
        '  "name": "...",\n'
        '  "type": "definition|formula|method|assumption|limitation|metric",\n'
        '  "content": "structured bullets or short paragraphs",\n'
        '  "evidence": [1,2]\n'
        "}\n"
        "Write the content field in English, keep keys in English.\n"
        "Use evidence indices from the provided context, and keep cards concise.\n"
        f"\nContext:\n{context}\n"
    )
