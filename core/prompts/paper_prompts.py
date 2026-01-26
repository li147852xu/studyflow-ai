from __future__ import annotations

from core.prompts.instructions import (
    general_knowledge_label,
    grounded_label,
    language_instruction,
    rag_balance_instruction,
    normalize_language,
)


def metadata_fallback_prompt(text: str) -> str:
    return (
        "Extract paper metadata from the text. Output JSON with keys: "
        "title, authors, year. If unknown, use \"unknown\".\n\n"
        f"Text:\n{text}\n"
    )


def paper_card_prompt(context: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是论文助理，请基于上下文生成 PAPER_CARD。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "要求：\n"
            "1) Summary 一段 5-8 句。\n"
            "2) Key contributions（贡献1/2/3）。\n"
            "3) Strengths / Weaknesses（各 3-6 条）。\n"
            "4) Extension ideas（3-6 条）。\n"
            "5) 每条必须带引用编号 [1][2]。\n"
            f"6) 如需补充通用知识，请单独增加“{general_knowledge_label(lang)}”小节，不带引用。\n"
            "\n"
            f"上下文：\n{context}\n"
        )
    return (
        "You are a paper assistant. Generate a PAPER_CARD from the context.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Requirements:\n"
        "1) Summary paragraph with 5-8 sentences.\n"
        "2) Key contributions (1/2/3).\n"
        "3) Strengths / Weaknesses (3-6 each).\n"
        "4) Extension ideas (3-6).\n"
        "5) Every bullet must include citation markers [1][2].\n"
        f"6) If adding general knowledge, add a '{general_knowledge_label(lang)}' section without citations.\n"
        "\n"
        f"Context:\n{context}\n"
    )


def aggregator_prompt(context: str, question: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是论文综述助理，请基于上下文回答聚合问题。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "要求：\n"
            "1) 输出四个部分：共识 / 分歧 / 方法路线分支 / related work 分段草稿。\n"
            "2) 每条必须带引用编号 [1][2]。\n"
            "3) 输出结构清晰，条目化。\n"
            f"4) 如需补充通用知识，请单独增加“{general_knowledge_label(lang)}”小节，不带引用。\n"
            "\n"
            f"聚合问题：{question}\n\n"
            f"上下文：\n{context}\n"
        )
    return (
        "You are a related work assistant. Answer the aggregation question using context.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Requirements:\n"
        "1) Output four sections: Consensus / Disagreements / Method branches / Related work draft.\n"
        "2) Every item must include citation markers [1][2].\n"
        "3) Keep structure clear and bulletized.\n"
        f"4) If adding general knowledge, add a '{general_knowledge_label(lang)}' section without citations.\n"
        "\n"
        f"Aggregation question: {question}\n\n"
        f"Context:\n{context}\n"
    )
