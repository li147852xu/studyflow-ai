from __future__ import annotations


def overview_prompt(context: str, topics: list[str]) -> str:
    topic_lines = "\n".join(f"- {topic}" for topic in topics)
    return (
        "你是课程助教。请基于给定上下文，用中文为主（保留英文术语）生成课程总览。\n"
        "要求：\n"
        "1) 输出结构：课程总览 -> 讲次/主题列表 -> 每讲 5-10 条要点。\n"
        "2) 每条要点必须带引用编号，例如 [1][2]。\n"
        "3) 内容长度控制在 1-3 屏。\n"
        "\n"
        f"主题列表（可适当调整）：\n{topic_lines}\n\n"
        f"上下文：\n{context}\n"
    )


def cheatsheet_prompt(context: str) -> str:
    return (
        "你是课程助教。请基于给定上下文，用中文为主（保留英文术语）生成考试速查表。\n"
        "要求：\n"
        "1) 必须包含四个部分：Definitions / Key Formulas / Typical Question Types / Common Pitfalls。\n"
        "2) 每条要点必须带引用编号，例如 [1][2]。\n"
        "3) 内容长度控制在 1-3 屏。\n"
        "\n"
        f"上下文：\n{context}\n"
    )


def explain_prompt(selection: str, mode: str, context: str | None = None) -> str:
    base = (
        "你是课程助教，请用中文为主（保留英文术语）解释下面的内容。\n"
        f"模式：{mode}\n"
        "模式说明：\n"
        "- plain：直白解释\n"
        "- example：给出例子辅助理解\n"
        "- pitfall：说明易错点或误区\n"
        "- link_prev：与前文/已学概念建立联系\n"
        "输出需要简洁、分点。\n"
    )
    if context:
        return f"{base}\n上下文：\n{context}\n\n内容：\n{selection}\n"
    return f"{base}\n内容：\n{selection}\n"
