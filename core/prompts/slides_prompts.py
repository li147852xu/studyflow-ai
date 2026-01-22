from __future__ import annotations


def slides_prompt(context: str, page_count: int) -> str:
    return (
        "你是演示稿助理，请基于上下文生成 Marp slides。\n"
        "要求：\n"
        f"1) 总页数约 {page_count} 页。\n"
        "2) 每页包含标题和 3-5 个要点。\n"
        "3) 每页必须带引用编号 [1][2]。\n"
        "4) 每页包含 speaker notes（使用 'Notes:' 开头）。\n"
        "5) 输出需包含 Marp front matter。\n"
        "6) 使用 '---' 作为页分隔符。\n"
        "\n"
        f"上下文：\n{context}\n"
    )


def qa_prompt(context: str) -> str:
    return (
        "基于上下文生成 10 条可能被问到的问题及简短回答要点，中文为主保留英文术语。\n"
        "格式：Q1: ... A: ...\n"
        "每条带引用编号 [1][2]。\n"
        "\n"
        f"上下文：\n{context}\n"
    )
