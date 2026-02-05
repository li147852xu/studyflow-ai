from __future__ import annotations

import json
from datetime import datetime, timezone

from core.domains.research import (
    add_idea_dialogue,
    confirm_idea,
    create_deck,
    create_experiment_plan,
    create_experiment_run,
    create_idea,
    create_paper_card,
)
from core.index_assets.store import get_doc_index_assets
from core.rag import map_reduce_project_query
from infra.db import get_connection
from service.asset_service import create_asset_version
from service.recent_activity_service import add_activity
from service.chat_service import ChatConfigError, chat


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_workspace(project_id: str) -> str:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT workspace_id FROM research_project WHERE id = ?",
            (project_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("Project not found.")
    return row["workspace_id"]


def generate_paper_card(*, workspace_id: str, paper_id: str, doc_id: str) -> dict:
    assets = get_doc_index_assets(doc_id) or {}
    prompt = (
        "Generate a structured paper card with: summary, contributions, strengths, weaknesses, and extension ideas.\n"
        f"Summary:\n{assets.get('summary_text') or ''}\n"
        f"Outline:\n{json.dumps(assets.get('outline') or {}, ensure_ascii=False)}\n"
        f"Entities: {', '.join(assets.get('entities') or [])}"
    )
    try:
        content = chat(prompt=prompt, max_tokens=900, temperature=0.2)
    except ChatConfigError:
        content = (
            "Summary:\n- \n\nContributions:\n- \n\nStrengths:\n- \n\nWeaknesses:\n- \n\nExtensions:\n- "
        )
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="paper_card",
        ref_id=f"paper:{paper_id}",
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
    create_paper_card(paper_id=paper_id, card_md_ref=version.id)
    add_activity(
        workspace_id=workspace_id,
        type="paper_card",
        title="Paper Card",
        status="succeeded",
        output_ref=json.dumps({"asset_version_id": version.id, "paper_id": paper_id}),
    )
    return {"content": content, "asset_version_id": version.id}


def generate_related_work(
    *, workspace_id: str, project_id: str
) -> dict:
    result = map_reduce_project_query(
        workspace_id=workspace_id,
        project_id=project_id,
        query="Related work for the entire project",
        map_tokens=250,
        reduce_tokens=600,
    )
    return {"answer": result.answer, "coverage": result.coverage, "citations": result.citations}


def create_idea_from_prompt(
    *,
    project_id: str,
    prompt: str,
) -> dict:
    idea_title = "Candidate Idea"
    claim = prompt.strip()
    try:
        response = chat(
            prompt=f"Propose a concise idea title and claim. Prompt: {prompt}",
            max_tokens=200,
            temperature=0.4,
        )
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        if lines:
            idea_title = lines[0][:80]
        if len(lines) > 1:
            claim = lines[1][:500]
    except ChatConfigError:
        pass
    idea_id = create_idea(
        project_id=project_id,
        title=idea_title,
        claim=claim,
        novelty_type="candidate",
        status="draft",
        version=1,
    )
    add_idea_dialogue(idea_id=idea_id, turn_no=1, role="user", content=prompt)
    add_idea_dialogue(idea_id=idea_id, turn_no=2, role="assistant", content=claim)
    version = create_asset_version(
        workspace_id=_project_workspace(project_id),
        kind="idea",
        ref_id=f"idea:{idea_id}",
        content=f"{idea_title}\n\n{claim}",
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
        workspace_id=_project_workspace(project_id),
        type="idea_candidate",
        title=idea_title,
        status="succeeded",
        output_ref=json.dumps({"idea_id": idea_id, "asset_version_id": version.id}),
    )
    return {"idea_id": idea_id, "title": idea_title, "claim": claim}


def confirm_idea_version(*, idea_id: str, version: int) -> None:
    confirm_idea(idea_id=idea_id, version=version)


def generate_experiment_plan_from_idea(
    *,
    project_id: str,
    idea_id: str,
    idea_claim: str,
) -> dict:
    prompt = (
        "Create an experiment plan in JSON with keys: hypothesis, dataset, metrics, baselines, ablations, expected_outcomes.\n"
        f"Idea: {idea_claim}"
    )
    try:
        response = chat(prompt=prompt, max_tokens=600, temperature=0.2)
        plan = {"raw": response}
    except ChatConfigError:
        plan = {
            "hypothesis": "",
            "dataset": "",
            "metrics": [],
            "baselines": [],
            "ablations": [],
            "expected_outcomes": "",
        }
    plan_id = create_experiment_plan(project_id=project_id, idea_id=idea_id, plan=plan)
    version = create_asset_version(
        workspace_id=_project_workspace(project_id),
        kind="experiment_plan",
        ref_id=f"plan:{plan_id}",
        content=json.dumps(plan, ensure_ascii=False, indent=2),
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
        workspace_id=_project_workspace(project_id),
        type="experiment_plan",
        title="Experiment Plan",
        status="succeeded",
        output_ref=json.dumps(
            {"plan_id": plan_id, "idea_id": idea_id, "asset_version_id": version.id}
        ),
    )
    return {"plan_id": plan_id, "plan": plan}


def add_experiment_run(
    *,
    project_id: str,
    plan_id: str | None,
    date: str,
    result: str,
    notes: str,
    next_action: str,
) -> dict:
    run_id = create_experiment_run(
        project_id=project_id,
        plan_id=plan_id,
        date=date,
        result=result,
        notes=notes,
        next_action=next_action,
    )
    add_activity(
        workspace_id=_project_workspace(project_id),
        type="experiment_run",
        title="Experiment Run",
        status="succeeded",
        output_ref=json.dumps({"run_id": run_id}),
    )
    return {"run_id": run_id, "created_at": _now_iso()}


def generate_deck(
    *,
    workspace_id: str,
    source_kind: str,
    source_ids: list[str],
    duration: int | None,
    coverage: dict | None,
) -> dict:
    title = "StudyFlow Deck"
    scope_line = f"Scope: {source_kind} · {', '.join(source_ids)}"
    citations_block = ""
    if coverage and coverage.get("included_docs"):
        citations_block = "\n".join([f"- {doc_id}" for doc_id in coverage["included_docs"]])
    content = (
        "---\n"
        "marp: true\n"
        "theme: default\n"
        "---\n"
        f"# {title}\n\n"
        f"{scope_line}\n\n"
        "## Agenda\n"
        "- Overview\n"
        "- Key Findings\n"
        "- Next Steps\n"
        "\n---\n"
        "## Citations\n"
        f"{citations_block}\n"
    )
    version = create_asset_version(
        workspace_id=workspace_id,
        kind="deck",
        ref_id=f"deck:{source_kind}:{','.join(source_ids)}",
        content=content,
        content_type="markdown",
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
    deck_id = create_deck(
        workspace_id=workspace_id,
        source_kind=source_kind,
        source_ids=source_ids,
        duration=duration,
        deck_md_ref=version.id,
        notes_ref=None,
        qa_ref=None,
        coverage_json=coverage,
    )
    add_activity(
        workspace_id=workspace_id,
        type="deck",
        title="Deck",
        status="succeeded",
        output_ref=json.dumps({"asset_version_id": version.id, "deck_id": deck_id}),
    )
    return {"deck_id": deck_id, "deck_ref": version.id, "content": content}
