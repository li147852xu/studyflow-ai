from __future__ import annotations


def metadata_fallback_prompt(text: str) -> str:
    return (
        "Extract paper metadata from the text. Output JSON with keys: "
        "title, authors, year. If unknown, use \"unknown\".\n\n"
        f"Text:\n{text}\n"
    )


def paper_card_prompt(context: str) -> str:
    return (
        "你是论文助理，请基于上下文生成 PAPER_CARD，中文为主保留英文术语。\n"
        "要求：\n"
        "1) Summary 一段 5-8 句。\n"
        "2) Key contributions（贡献1/2/3）。\n"
        "3) Strengths / Weaknesses（各 3-6 条）。\n"
        "4) Extension ideas（3-6 条）。\n"
        "5) 每条必须带引用编号 [1][2]。\n"
        "\n"
        f"上下文：\n{context}\n"
    )


def aggregator_prompt(context: str, question: str) -> str:
    return (
        "你是论文综述助理，请基于上下文回答聚合问题，中文为主保留英文术语。\n"
        "要求：\n"
        "1) 输出四个部分：共识 / 分歧 / 方法路线分支 / related work 分段草稿。\n"
        "2) 每条必须带引用编号 [1][2]。\n"
        "3) 输出结构清晰，条目化。\n"
        "\n"
        f"聚合问题：{question}\n\n"
        f"上下文：\n{context}\n"
    )
