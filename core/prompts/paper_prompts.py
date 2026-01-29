from __future__ import annotations

from core.prompts.instructions import (
    general_knowledge_label,
    language_instruction,
    normalize_language,
    rag_balance_instruction,
)


def metadata_fallback_prompt(text: str) -> str:
    return (
        "Extract paper metadata from the text. Output JSON with keys: "
        'title, authors, year. If unknown, use "unknown".\n\n'
        f"Text:\n{text}\n"
    )


def paper_card_prompt(context: str, language: str = "en") -> str:
    lang = normalize_language(language)
    gk_label = general_knowledge_label(lang)
    if lang == "zh":
        return (
            "你是论文助理，请基于上下文生成论文卡片。\n"
            + f"{language_instruction(lang)}\n"
            + f"{rag_balance_instruction(lang)}"
            + "请使用以下精确的格式输出：\n\n"
            + "Summary:\n(5-8句的摘要段落)\n\n"
            + "Contributions:\n- 贡献点1 [引用]\n- 贡献点2 [引用]\n- 贡献点3 [引用]\n\n"
            + "Strengths:\n- 优点1 [引用]\n- 优点2 [引用]\n- 优点3 [引用]\n\n"
            + "Weaknesses:\n- 缺点1 [引用]\n- 缺点2 [引用]\n- 缺点3 [引用]\n\n"
            + "Extensions:\n- 扩展思路1 [引用]\n- 扩展思路2 [引用]\n- 扩展思路3 [引用]\n\n"
            + "要求：\n"
            + "- 每条必须带引用编号如 [1][2]\n"
            + f'- 如需补充通用知识，请单独增加"{gk_label}"小节，不带引用\n'
            + "\n"
            + f"上下文：\n{context}\n"
        )
    return (
        "You are a paper assistant. Generate a paper card from the context.\n"
        + f"{language_instruction(lang)}\n"
        + f"{rag_balance_instruction(lang)}"
        + "Use EXACTLY this format:\n\n"
        + "Summary:\n(5-8 sentence summary paragraph)\n\n"
        + "Contributions:\n- Contribution 1 [citation]\n- Contribution 2 [citation]\n- Contribution 3 [citation]\n\n"
        + "Strengths:\n- Strength 1 [citation]\n- Strength 2 [citation]\n- Strength 3 [citation]\n\n"
        + "Weaknesses:\n- Weakness 1 [citation]\n- Weakness 2 [citation]\n- Weakness 3 [citation]\n\n"
        + "Extensions:\n- Extension idea 1 [citation]\n- Extension idea 2 [citation]\n- Extension idea 3 [citation]\n\n"
        + "Requirements:\n"
        + "- Every bullet must include citation markers like [1][2]\n"
        + f"- If adding general knowledge, add a '{gk_label}' section without citations\n"
        + "\n"
        + f"Context:\n{context}\n"
    )


def aggregator_prompt(context: str, question: str, language: str = "en") -> str:
    lang = normalize_language(language)
    gk_label = general_knowledge_label(lang)
    if lang == "zh":
        return (
            "你是论文综述助理，请基于上下文回答聚合问题。\n"
            + f"{language_instruction(lang)}\n"
            + f"{rag_balance_instruction(lang)}"
            + "要求：\n"
            + "1) 输出四个部分：共识 / 分歧 / 方法路线分支 / related work 分段草稿。\n"
            + "2) 每条必须带引用编号 [1][2]。\n"
            + "3) 输出结构清晰，条目化。\n"
            + f'4) 如需补充通用知识，请单独增加"{gk_label}"小节，不带引用。\n'
            + "\n"
            + f"聚合问题：{question}\n\n"
            + f"上下文：\n{context}\n"
        )
    return (
        "You are a related work assistant. Answer the aggregation question using context.\n"
        + f"{language_instruction(lang)}\n"
        + f"{rag_balance_instruction(lang)}"
        + "Requirements:\n"
        + "1) Output four sections: Consensus / Disagreements / Method branches / Related work draft.\n"
        + "2) Every item must include citation markers [1][2].\n"
        + "3) Keep structure clear and bulletized.\n"
        + f"4) If adding general knowledge, add a '{gk_label}' section without citations.\n"
        + "\n"
        + f"Aggregation question: {question}\n\n"
        + f"Context:\n{context}\n"
    )
