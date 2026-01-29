from __future__ import annotations

from core.prompts.instructions import (
    general_knowledge_label,
    language_instruction,
    normalize_language,
    rag_balance_instruction,
)


def slides_prompt(context: str, page_count: int, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是演示稿助理，请基于上下文生成 Marp slides。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "格式要求（必须严格遵守）：\n"
            "1) 只输出 Marp Markdown，不要额外解释。\n"
            f"2) 总页数严格为 {page_count} 页（不含封面外的多余页）。\n"
            "3) 每页结构必须是：标题行 + 3-5 个要点（使用 '-' 列表）。\n"
            "4) 引用必须出现在要点末尾，格式如 [1]。\n"
            "5) 每页必须包含 speaker notes，使用以下格式：\n"
            "   Notes:\n"
            "   - 说明或补充\n"
            "6) 如需通用知识，请在 Notes 中单独标注“{general}”，不得加引用。\n"
            "7) 必须包含 Marp front matter，且使用 '---' 作为页分隔符。\n"
            "\n"
            "Marp 模板（严格对齐）：\n"
            "---\n"
            "marp: true\n"
            "paginate: true\n"
            "theme: default\n"
            "---\n"
            "# 标题\n"
            "- 要点 1 [1]\n"
            "- 要点 2 [2]\n"
            "Notes:\n"
            f"- {general_knowledge_label(lang)}: 可选补充\n"
            "---\n"
            "# 下一页标题\n"
            "- 要点 1 [3]\n"
            "Notes:\n"
            "- ...\n"
            "\n"
            "\n"
            f"上下文：\n{context}\n"
        )
    return (
        "You are a presentation assistant. Generate Marp slides using the context.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Format requirements (strict):\n"
        "1) Output Marp Markdown only, no extra commentary.\n"
        f"2) Total pages must be exactly {page_count} (no extra slides).\n"
        "3) Each slide structure: title line + 3-5 bullets (use '-' list).\n"
        "4) Citations must appear at the end of bullets, e.g. [1].\n"
        "5) Each slide must include speaker notes in this format:\n"
        "   Notes:\n"
        "   - explanation\n"
        f"6) If adding general knowledge, mark it in Notes as '{general_knowledge_label(lang)}' with no citations.\n"
        "7) Include Marp front matter and use '---' as slide separators.\n"
        "\n"
        "Marp template (match exactly):\n"
        "---\n"
        "marp: true\n"
        "paginate: true\n"
        "theme: default\n"
        "---\n"
        "# Title\n"
        "- Bullet 1 [1]\n"
        "- Bullet 2 [2]\n"
        "Notes:\n"
        f"- {general_knowledge_label(lang)}: optional\n"
        "---\n"
        "# Next title\n"
        "- Bullet 1 [3]\n"
        "Notes:\n"
        "- ...\n"
        "\n"
        f"Context:\n{context}\n"
    )


def qa_prompt(context: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "基于上下文生成 10 条可能被问到的问题及简短回答要点。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "格式：Q1: ... A: ...\n"
            "有据内容必须带引用编号 [1][2]。\n"
            f"如需补充通用知识，请在答案中标注“{general_knowledge_label(lang)}”，不得加引用。\n"
            "\n"
            f"上下文：\n{context}\n"
        )
    return (
        "Generate 10 likely questions with brief answer bullets based on context.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Format: Q1: ... A: ...\n"
        "Grounded answers must include citation markers [1][2].\n"
        f"If adding general knowledge, label it as '{general_knowledge_label(lang)}' with no citations.\n"
        "\n"
        f"Context:\n{context}\n"
    )
