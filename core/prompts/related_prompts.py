from __future__ import annotations

from core.prompts.instructions import language_instruction, normalize_language


def related_create_prompt(context: str, topic: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你正在基于提供的来源撰写 related work。\n"
            f"{language_instruction(lang)}\n"
            "仅返回 JSON，字段包括：comparison_axes（字符串列表）、sections（{title, bullets} 列表）、draft（字符串）。\n"
            "bullets 与 draft 中使用引用编号 [1][2]。\n"
            "JSON 的键名保持英文，内容使用中文。\n"
            f"\n主题：\n{topic}\n\n上下文：\n{context}\n"
        )
    return (
        "You are drafting a related work section using provided sources.\n"
        f"{language_instruction(lang)}\n"
        "Return JSON only with fields: comparison_axes (list of strings), "
        "sections (list of {title, bullets}), draft (string).\n"
        "Use citation indices like [1][2] in bullets and draft.\n"
        "Keep JSON keys in English; write content in English.\n"
        f"\nTopic:\n{topic}\n\nContext:\n{context}\n"
    )


def related_update_prompt(
    context: str, topic: str, existing_outline: str, language: str = "en"
) -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你正在基于新论文更新 related work 大纲和草稿。\n"
            f"{language_instruction(lang)}\n"
            "仅返回 JSON，字段包括：insert_suggestions（列表）、sections（{title, bullets} 列表）、draft（字符串）。\n"
            "使用引用编号 [1][2]。\n"
            "JSON 的键名保持英文，内容使用中文。\n"
            f"\n主题：\n{topic}\n\n已有大纲：\n{existing_outline}\n\n上下文：\n{context}\n"
        )
    return (
        "You are updating a related work outline and draft with new papers.\n"
        f"{language_instruction(lang)}\n"
        "Return JSON only with fields: insert_suggestions (list), sections (list of {title, bullets}), draft (string).\n"
        "Use citation indices like [1][2].\n"
        "Keep JSON keys in English; write content in English.\n"
        f"\nTopic:\n{topic}\n\nExisting outline:\n{existing_outline}\n\nContext:\n{context}\n"
    )
