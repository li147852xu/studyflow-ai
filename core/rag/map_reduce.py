from __future__ import annotations

import json
from dataclasses import dataclass

from core.ui_state.storage import get_setting
from infra.db import get_connection
from service.chat_service import ChatConfigError, chat


def _get_output_language(workspace_id: str | None) -> str:
    """Get the output language from settings, default to 'en'."""
    if workspace_id:
        lang = get_setting(workspace_id, "output_language")
        if lang:
            return lang
    return get_setting(None, "output_language") or "en"


@dataclass
class MapReduceResult:
    answer: str
    coverage: dict
    citations: list[dict]
    map_outputs: list[dict]


def _load_index_assets(doc_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT summary_text, outline_json, entities_json
            FROM doc_index_assets
            WHERE doc_id = ?
            """,
            (doc_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "summary_text": row["summary_text"],
        "outline": json.loads(row["outline_json"]) if row["outline_json"] else None,
        "entities": json.loads(row["entities_json"]) if row["entities_json"] else None,
    }


def _doc_meta(doc_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, filename, file_type, doc_type FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
    return dict(row) if row else None


def _map_prompt(query: str, assets: dict, title: str, language: str = "en") -> str:
    summary = assets.get("summary_text") or ""
    outline = assets.get("outline") or {}
    entities = assets.get("entities") or []

    if language == "zh":
        return (
            "你正在创建一个简短的证据笔记，用于整课程/项目级别的 map-reduce 答案生成。\n"
            f"文档: {title}\n"
            f"查询: {query}\n"
            f"摘要:\n{summary}\n"
            f"大纲:\n{json.dumps(outline, ensure_ascii=False)}\n"
            f"关键实体: {', '.join(entities)}\n\n"
            "请返回与查询相关的要点列表，使用中文输出。"
        )
    return (
        "You are creating a short, course/project-wide evidence note for a map-reduce answer.\n"
        f"Document: {title}\n"
        f"Query: {query}\n"
        f"Summary:\n{summary}\n"
        f"Outline:\n{json.dumps(outline, ensure_ascii=False)}\n"
        f"Key entities: {', '.join(entities)}\n\n"
        "Return a concise bullet list of key points relevant to the query."
    )


def _reduce_prompt(query: str, map_outputs: list[dict], language: str = "en") -> str:
    bullets = "\n".join(
        f"- {item['title']}: {item['content']}" for item in map_outputs if item.get("content")
    )

    if language == "zh":
        return (
            "你正在将多个证据笔记汇总成最终答案。\n"
            f"查询: {query}\n"
            "证据笔记:\n"
            f"{bullets}\n\n"
            "请返回结构化、简洁的中文回答，包含标题和可操作要点。"
        )
    return (
        "You are reducing evidence notes into a final answer.\n"
        f"Query: {query}\n"
        "Evidence notes:\n"
        f"{bullets}\n\n"
        "Return a structured, concise response with headings and actionable points."
    )


def _map_doc(query: str, doc_id: str, map_tokens: int, language: str = "en") -> dict:
    meta = _doc_meta(doc_id) or {"filename": doc_id}
    assets = _load_index_assets(doc_id) or {"summary_text": "", "outline": {}, "entities": []}
    title = meta.get("filename") or doc_id
    prompt = _map_prompt(query, assets, title, language)
    try:
        content = chat(prompt=prompt, max_tokens=map_tokens, temperature=0.2)
    except ChatConfigError:
        content = (assets.get("summary_text") or "")[:500]
    return {
        "doc_id": doc_id,
        "title": title,
        "content": content.strip(),
        "snippet": (assets.get("summary_text") or "")[:240],
    }


def _reduce(query: str, map_outputs: list[dict], reduce_tokens: int, language: str = "en") -> str:
    prompt = _reduce_prompt(query, map_outputs, language)
    try:
        return chat(prompt=prompt, max_tokens=reduce_tokens, temperature=0.2).strip()
    except ChatConfigError:
        combined = "\n".join([item["content"] for item in map_outputs if item["content"]])
        return combined[:2000]


def map_reduce_course_query(
    *,
    workspace_id: str,
    course_id: str,
    query: str,
    map_tokens: int,
    reduce_tokens: int,
) -> MapReduceResult:
    language = _get_output_language(workspace_id)

    with get_connection() as connection:
        lecture_rows = connection.execute(
            """
            SELECT lecture.id, lecture.lecture_no, lecture.topic
            FROM lecture
            WHERE lecture.course_id = ?
            ORDER BY lecture.lecture_no, lecture.date
            """,
            (course_id,),
        ).fetchall()
        doc_rows = connection.execute(
            """
            SELECT lecture.id as lecture_id, lecture_material.doc_id
            FROM lecture
            LEFT JOIN lecture_material ON lecture_material.lecture_id = lecture.id
            WHERE lecture.course_id = ?
            """,
            (course_id,),
        ).fetchall()
    lecture_docs: dict[str, list[str]] = {}
    for row in doc_rows:
        lecture_docs.setdefault(row["lecture_id"], [])
        if row["doc_id"]:
            lecture_docs[row["lecture_id"]].append(row["doc_id"])

    included_docs: list[str] = []
    missing_docs: list[str] = []
    per_lecture: list[dict] = []
    map_outputs: list[dict] = []

    missing_lectures: list[str] = []
    for lecture in lecture_rows:
        doc_ids = lecture_docs.get(lecture["id"], [])
        included_count = 0
        if not doc_ids:
            missing_lectures.append(lecture["id"])
        for doc_id in doc_ids:
            assets = _load_index_assets(doc_id)
            if not assets:
                missing_docs.append(doc_id)
                continue
            included_docs.append(doc_id)
            included_count += 1
            map_outputs.append(_map_doc(query, doc_id, map_tokens, language))
        if included_count == 0:
            missing_lectures.append(lecture["id"])
        per_lecture.append(
            {
                "lecture_id": lecture["id"],
                "lecture_no": lecture["lecture_no"],
                "topic": lecture["topic"],
                "evidence_count": included_count,
            }
        )

    answer = _reduce(query, map_outputs, reduce_tokens, language)
    citations = [
        {"doc_id": item["doc_id"], "title": item["title"], "snippet": item["snippet"]}
        for item in map_outputs
    ]
    coverage = {
        "scope": "course",
        "included_docs": list(dict.fromkeys(included_docs)),
        "missing_docs": list(dict.fromkeys(missing_docs)),
        "per_lecture": per_lecture,
        "missing_lectures": list(dict.fromkeys(missing_lectures)),
    }
    return MapReduceResult(answer=answer, coverage=coverage, citations=citations, map_outputs=map_outputs)


def map_reduce_project_query(
    *,
    workspace_id: str,
    project_id: str,
    query: str,
    map_tokens: int,
    reduce_tokens: int,
) -> MapReduceResult:
    language = _get_output_language(workspace_id)

    with get_connection() as connection:
        paper_rows = connection.execute(
            """
            SELECT id, doc_id, title
            FROM papers
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()

    included_docs: list[str] = []
    missing_docs: list[str] = []
    per_paper: list[dict] = []
    map_outputs: list[dict] = []

    for paper in paper_rows:
        doc_id = paper["doc_id"]
        if not doc_id:
            continue
        assets = _load_index_assets(doc_id)
        if not assets:
            missing_docs.append(doc_id)
            per_paper.append({"paper_id": paper["id"], "title": paper["title"], "evidence_count": 0})
            continue
        included_docs.append(doc_id)
        map_outputs.append(_map_doc(query, doc_id, map_tokens, language))
        per_paper.append({"paper_id": paper["id"], "title": paper["title"], "evidence_count": 1})

    answer = _reduce(query, map_outputs, reduce_tokens, language)
    citations = [
        {"doc_id": item["doc_id"], "title": item["title"], "snippet": item["snippet"]}
        for item in map_outputs
    ]
    coverage = {
        "scope": "project",
        "included_docs": list(dict.fromkeys(included_docs)),
        "missing_docs": list(dict.fromkeys(missing_docs)),
        "per_paper": per_paper,
    }
    return MapReduceResult(answer=answer, coverage=coverage, citations=citations, map_outputs=map_outputs)
