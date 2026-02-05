from __future__ import annotations

import json
from datetime import datetime, timezone

from core.assets.store import get_asset_by_ref, list_asset_versions, read_asset_content
from core.domains.course import upsert_exam_asset
from core.index_assets.store import get_doc_index_assets
from core.rag import map_reduce_course_query
from core.ui_state.storage import get_setting
from infra.db import get_connection
from service.asset_service import create_asset_version
from service.recent_activity_service import add_activity
from core.agents.course_agent import CourseAgent
from service.metadata_service import llm_metadata
from core.quality.citations_check import check_citations
from core.telemetry.run_logger import log_run
from service.chat_service import ChatConfigError, chat


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _course_doc_ids(course_id: str) -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT doc_id FROM (
              SELECT lecture_material.doc_id as doc_id
              FROM lecture_material
              JOIN lecture ON lecture.id = lecture_material.lecture_id
              WHERE lecture.course_id = ?
              UNION
              SELECT course_documents.doc_id as doc_id
              FROM course_documents
              WHERE course_documents.course_id = ?
            )
            """,
            (course_id, course_id),
        ).fetchall()
    return [row["doc_id"] for row in rows]


def generate_exam_blueprint(*, workspace_id: str, course_id: str) -> dict:
    map_tokens = int(get_setting(workspace_id, "rag_map_tokens") or 250)
    reduce_tokens = int(get_setting(workspace_id, "rag_reduce_tokens") or 600)
    output_lang = get_setting(workspace_id, "output_language") or "en"
    
    # Build query in appropriate language
    if output_lang == "zh":
        query = "整门课程的考试大纲，包括考试范围、重要概念、题型分布、复习重点等"
    else:
        query = "Exam blueprint for the whole course, including scope, key concepts, question types, and study focus"
    
    result = map_reduce_course_query(
        workspace_id=workspace_id,
        course_id=course_id,
        query=query,
        map_tokens=map_tokens,
        reduce_tokens=reduce_tokens,
    )
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="exam_blueprint",
        ref_id=f"course_exam:{course_id}",
        content=result.answer,
        content_type="text",
        run_id=None,
        model=None,
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode="map_reduce",
        embed_model=None,
        seed=None,
        prompt_version="v3",
        hits=[],
    )
    upsert_exam_asset(
        course_id=course_id,
        blueprint_ref=version.id,
        cheatsheet_ref=None,
        coverage_json=json.dumps(result.coverage, ensure_ascii=False),
    )
    add_activity(
        workspace_id=workspace_id,
        type="exam_blueprint",
        title="Exam Blueprint",
        status="succeeded",
        output_ref=json.dumps({"asset_version_id": version.id, "course_id": course_id}),
    )
    return {
        "answer": result.answer,
        "coverage": result.coverage,
        "citations": result.citations,
        "asset_version_id": version.id,
    }


def generate_assignment_analysis(
    *,
    workspace_id: str,
    assignment_id: str,
    title: str,
) -> dict:
    output_lang = get_setting(workspace_id, "output_language") or "en"
    
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT assignment_asset.doc_id, documents.filename
            FROM assignment_asset
            JOIN documents ON documents.id = assignment_asset.doc_id
            WHERE assignment_asset.assignment_id = ?
            """,
            (assignment_id,),
        ).fetchall()
    summaries = []
    for row in rows:
        assets = get_doc_index_assets(row["doc_id"])
        if assets and assets.get("summary_text"):
            summaries.append(f"{row['filename']}: {assets['summary_text']}")
    
    if output_lang == "zh":
        prompt = (
            "你正在分析一份作业。请提供：问题拆解、评分标准、常见陷阱、解题框架。\n"
            "不要提供完整答案。\n"
            f"作业: {title}\n"
            f"参考资料:\n{chr(10).join(summaries)}"
        )
        fallback_content = (
            "问题拆解:\n- 总结任务要点。\n\n"
            "评分标准:\n- 识别关键评分点。\n\n"
            "常见陷阱:\n- 注意常见错误。\n\n"
            "解题框架:\n- 列出步骤但不提供完整答案。"
        )
    else:
        prompt = (
            "You are analyzing an assignment. Provide: problem breakdown, grading rubric, common pitfalls, and a solution framework.\n"
            "Do NOT provide full final answers.\n"
            f"Assignment: {title}\n"
            f"References:\n{chr(10).join(summaries)}"
        )
        fallback_content = (
            "Problem breakdown:\n- Summarize the tasks.\n\n"
            "Grading rubric:\n- Identify key evaluation points.\n\n"
            "Common pitfalls:\n- Note common mistakes.\n\n"
            "Solution framework:\n- Outline steps without full answers."
        )
    
    try:
        content = chat(prompt=prompt, max_tokens=700, temperature=0.2)
    except ChatConfigError:
        content = fallback_content
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="assignment_analysis",
        ref_id=f"assignment:{assignment_id}",
        content=content,
        content_type="text",
        run_id=None,
        model=None,
        provider=None,
        temperature=None,
        max_tokens=None,
        retrieval_mode=None,
        embed_model=None,
        seed=None,
        prompt_version="v3",
        hits=[],
    )
    add_activity(
        workspace_id=workspace_id,
        type="assignment_analysis",
        title=title,
        status="succeeded",
        output_ref=json.dumps({"asset_version_id": version.id, "assignment_id": assignment_id}),
    )
    return {"content": content, "asset_version_id": version.id, "created_at": _now_iso()}


def course_docs_for_qa(course_id: str) -> list[str]:
    return _course_doc_ids(course_id)


def get_persisted_course_overview(workspace_id: str, course_id: str) -> dict | None:
    """Retrieve the latest persisted course overview if exists."""
    ref_id = f"course_overview:{course_id}"
    asset = get_asset_by_ref(workspace_id, "course_overview", ref_id)
    if not asset:
        return None
    versions = list_asset_versions(asset.id)
    if not versions:
        return None
    latest = versions[0]  # Already sorted DESC
    content = read_asset_content(latest)
    citations = []
    if latest.citations_json:
        try:
            citations = json.loads(latest.citations_json)
        except json.JSONDecodeError:
            pass
    return {
        "content": content,
        "citations": citations,
        "asset_version_id": latest.id,
        "created_at": latest.created_at,
    }


def get_persisted_course_cheatsheet(workspace_id: str, course_id: str) -> dict | None:
    """Retrieve the latest persisted course cheatsheet if exists."""
    ref_id = f"course_cheatsheet:{course_id}"
    asset = get_asset_by_ref(workspace_id, "course_cheatsheet", ref_id)
    if not asset:
        return None
    versions = list_asset_versions(asset.id)
    if not versions:
        return None
    latest = versions[0]
    content = read_asset_content(latest)
    citations = []
    if latest.citations_json:
        try:
            citations = json.loads(latest.citations_json)
        except json.JSONDecodeError:
            pass
    return {
        "content": content,
        "citations": citations,
        "asset_version_id": latest.id,
        "created_at": latest.created_at,
    }


def generate_course_overview(*, workspace_id: str, course_id: str) -> dict:
    doc_ids = _course_doc_ids(course_id)
    if not doc_ids:
        return {"error": "missing_materials"}
    retrieval_mode = get_setting(workspace_id, "retrieval_mode") or "hybrid"
    agent = CourseAgent(workspace_id, course_id, doc_ids, retrieval_mode)
    output = agent.generate_overview()
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_overview",
        input_payload={"course_id": course_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=None,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_overview",
        ref_id=f"course_overview:{course_id}",
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v3",
        hits=output.hits,
    )
    add_activity(
        workspace_id=workspace_id,
        type="course_overview",
        title="Course Overview",
        status="succeeded",
        output_ref=json.dumps({"asset_version_id": version.id, "course_id": course_id}),
    )
    return {"content": output.content, "citations": output.citations, "asset_version_id": version.id}


def generate_course_cheatsheet(*, workspace_id: str, course_id: str) -> dict:
    doc_ids = _course_doc_ids(course_id)
    if not doc_ids:
        return {"error": "missing_materials"}
    retrieval_mode = get_setting(workspace_id, "retrieval_mode") or "hybrid"
    agent = CourseAgent(workspace_id, course_id, doc_ids, retrieval_mode)
    output = agent.generate_cheatsheet()
    meta = llm_metadata(temperature=0.2)
    citation_ok, citation_error = check_citations(output.content, output.hits)
    run_id = log_run(
        workspace_id=workspace_id,
        action_type="course_cheatsheet",
        input_payload={"course_id": course_id},
        retrieval_mode=output.retrieval_mode,
        hits=output.hits,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version,
        latency_ms=None,
        citation_incomplete=not citation_ok,
        errors=citation_error,
    )
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="course_cheatsheet",
        ref_id=f"course_cheatsheet:{course_id}",
        content=output.content,
        content_type="text",
        run_id=run_id,
        model=meta["model"],
        provider=meta["provider"],
        temperature=meta["temperature"],
        max_tokens=meta["max_tokens"],
        retrieval_mode=output.retrieval_mode,
        embed_model=meta["embed_model"],
        seed=meta["seed"],
        prompt_version=output.prompt_version or "v3",
        hits=output.hits,
    )
    add_activity(
        workspace_id=workspace_id,
        type="course_cheatsheet",
        title="Course Cheat Sheet",
        status="succeeded",
        output_ref=json.dumps({"asset_version_id": version.id, "course_id": course_id}),
    )
    return {"content": output.content, "citations": output.citations, "asset_version_id": version.id}
