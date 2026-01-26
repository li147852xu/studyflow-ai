from __future__ import annotations

from core.prompts.instructions import (
    general_knowledge_label,
    grounded_label,
    language_instruction,
    rag_balance_instruction,
    normalize_language,
)


def overview_prompt(context: str, topics: list[str], language: str = "en") -> str:
    topic_lines = "\n".join(f"- {topic}" for topic in topics)
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是课程助教。请基于给定上下文生成课程总览。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "要求：\n"
            "1) 输出结构：课程总览 -> 讲次/主题列表 -> 每讲 5-10 条要点。\n"
            "2) 课程总览与要点必须带引用编号，例如 [1][2]。\n"
            f"3) 如需补充通用知识，请单独增加“{general_knowledge_label(lang)}”小节，不带引用。\n"
            "4) 内容长度控制在 1-3 屏。\n"
            "\n"
            f"主题列表（可适当调整）：\n{topic_lines}\n\n"
            f"上下文：\n{context}\n"
        )
    return (
        "You are a course TA. Generate a course overview using the provided context.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Requirements:\n"
        "1) Structure: Course overview -> Lecture/topic list -> 5-10 bullet points per lecture.\n"
        "2) Overview and bullets must include citation markers like [1][2].\n"
        f"3) If adding general knowledge, add a separate section titled '{general_knowledge_label(lang)}' without citations.\n"
        "4) Keep length within 1-3 screens.\n"
        "\n"
        f"Topic list (can be adjusted):\n{topic_lines}\n\n"
        f"Context:\n{context}\n"
    )


def cheatsheet_prompt(context: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是课程助教。请基于给定上下文生成考试速查表。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "要求：\n"
            "1) 必须包含四个部分：Definitions / Key Formulas / Typical Question Types / Common Pitfalls。\n"
            "2) 每条要点必须带引用编号，例如 [1][2]。\n"
            f"3) 如需补充通用知识，请单独增加“{general_knowledge_label(lang)}”小节，不带引用。\n"
            "4) 内容长度控制在 1-3 屏。\n"
            "\n"
            f"上下文：\n{context}\n"
        )
    return (
        "You are a course TA. Create an exam cheat sheet from the context.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Requirements:\n"
        "1) Include sections: Definitions / Key Formulas / Typical Question Types / Common Pitfalls.\n"
        "2) Every bullet must include citation markers like [1][2].\n"
        f"3) If adding general knowledge, add a section titled '{general_knowledge_label(lang)}' without citations.\n"
        "4) Keep length within 1-3 screens.\n"
        "\n"
        f"Context:\n{context}\n"
    )


def explain_prompt(
    selection: str,
    mode: str,
    context: str | None = None,
    language: str = "en",
) -> str:
    lang = normalize_language(language)
    if lang == "zh":
        base = (
            "你是课程助教，请解释下面的内容。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            f"模式：{mode}\n"
            "模式说明：\n"
            "- plain：直白解释\n"
            "- example：给出例子辅助理解\n"
            "- pitfall：说明易错点或误区\n"
            "- link_prev：与前文/已学概念建立联系\n"
            "输出需要简洁、分点。\n"
            f"先输出“{grounded_label(lang)}”，必须带引用编号。\n"
            f"如需补充通用知识，追加“{general_knowledge_label(lang)}”小节，不带引用。\n"
        )
    else:
        base = (
            "You are a course TA. Explain the following content.\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            f"Mode: {mode}\n"
            "Mode guide:\n"
            "- plain: straightforward explanation\n"
            "- example: provide an example\n"
            "- pitfall: common pitfalls or mistakes\n"
            "- link_prev: link to earlier concepts\n"
            "Keep the output concise and bullet-based.\n"
            f"Start with a '{grounded_label(lang)}' section with citations.\n"
            f"If needed, add a '{general_knowledge_label(lang)}' section without citations.\n"
        )
    if context:
        return f"{base}\nContext:\n{context}\n\nContent:\n{selection}\n"
    return f"{base}\nContent:\n{selection}\n"
