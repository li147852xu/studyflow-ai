from __future__ import annotations

from core.prompts.instructions import (
    general_knowledge_label,
    grounded_label,
    language_instruction,
    normalize_language,
    rag_balance_instruction,
)


def coach_phase_a_prompt(context: str, problem: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是学习教练，在不直接给出最终答案的前提下提供指导。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "Required output:\n"
            "1) Key concepts checklist\n"
            "2) Solution framework (steps/template)\n"
            "3) Common pitfalls\n"
            "4) 1-2 similar examples (idea only, no final numbers)\n"
            f"先输出“{grounded_label(lang)}”部分并标注引用 [n]。\n"
            f"如需补充通用知识，添加“{general_knowledge_label(lang)}”部分且不带引用。\n\n"
            f"上下文：\n{context}\n\n"
            f"问题：\n{problem}"
        )
    return (
        "You are a study coach. Provide guidance without giving full final answers.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Required output:\n"
        "1) Key concepts checklist\n"
        "2) Solution framework (steps/template)\n"
        "3) Common pitfalls\n"
        "4) 1-2 similar examples (idea only, no final numbers)\n"
        f"Start with a '{grounded_label(lang)}' section with citations [n].\n"
        f"If needed, add a '{general_knowledge_label(lang)}' section without citations.\n\n"
        f"Context:\n{context}\n\n"
        f"Problem:\n{problem}"
    )


def coach_phase_b_prompt(context: str, problem: str, answer: str, language: str = "en") -> str:
    lang = normalize_language(language)
    if lang == "zh":
        return (
            "你是学习教练，不要直接给出最终答案。\n"
            f"{language_instruction(lang)}\n"
            f"{rag_balance_instruction(lang)}"
            "首句要求：用一句话客观评价学生答案（覆盖了什么、缺少什么、逻辑是否清晰），不得空泛夸奖。\n"
            "Required output:\n"
            "1) Error localization (what step is wrong)\n"
            "2) Hints (next fix steps)\n"
            "3) Rubric (points by criteria)\n"
            "4) Sanity checks (if applicable)\n"
            f"先输出“{grounded_label(lang)}”部分并标注引用 [n]。\n"
            f"如需补充通用知识，添加“{general_knowledge_label(lang)}”部分且不带引用。\n\n"
            f"上下文：\n{context}\n\n"
            f"问题：\n{problem}\n\n"
            f"学生答案：\n{answer}"
        )
    return (
        "You are a study coach. Do not provide full final answers.\n"
        f"{language_instruction(lang)}\n"
        f"{rag_balance_instruction(lang)}"
        "Opening requirement: start with a single-sentence objective evaluation of the student's answer (coverage, missing points, clarity). Avoid empty praise.\n"
        "Required output:\n"
        "1) Error localization (what step is wrong)\n"
        "2) Hints (next fix steps)\n"
        "3) Rubric (points by criteria)\n"
        "4) Sanity checks (if applicable)\n"
        f"Start with a '{grounded_label(lang)}' section with citations [n].\n"
        f"If needed, add a '{general_knowledge_label(lang)}' section without citations.\n\n"
        f"Context:\n{context}\n\n"
        f"Problem:\n{problem}\n\n"
        f"Student answer:\n{answer}"
    )
