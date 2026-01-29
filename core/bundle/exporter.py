from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from core.bundle.manifest import build_manifest, dump_manifest
from core.bundle.sanitizer import sanitize_dict
from infra.db import get_connection, get_workspaces_dir


def _fetch_rows(query: str, params: tuple) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def export_bundle(
    *,
    workspace_id: str,
    out_path: Path,
    with_pdf: bool,
    with_assets: bool,
    with_prompts: bool,
) -> Path:
    docs = _fetch_rows(
        "SELECT * FROM documents WHERE workspace_id = ?",
        (workspace_id,),
    )
    doc_ids = [doc["id"] for doc in docs]
    if doc_ids:
        placeholders = ",".join(["?"] * len(doc_ids))
        chunks = _fetch_rows(
            f"SELECT * FROM chunks WHERE doc_id IN ({placeholders})",
            tuple(doc_ids),
        )
        pages = _fetch_rows(
            f"SELECT * FROM document_pages WHERE doc_id IN ({placeholders})",
            tuple(doc_ids),
        )
        tags = _fetch_rows(
            f"SELECT * FROM document_tags WHERE doc_id IN ({placeholders})",
            tuple(doc_ids),
        )
    else:
        chunks, pages, tags = [], [], []

    courses = _fetch_rows(
        "SELECT * FROM courses WHERE workspace_id = ?",
        (workspace_id,),
    )
    course_ids = [course["id"] for course in courses]
    if course_ids:
        placeholders = ",".join(["?"] * len(course_ids))
        course_docs = _fetch_rows(
            f"SELECT * FROM course_documents WHERE course_id IN ({placeholders})",
            tuple(course_ids),
        )
    else:
        course_docs = []

    papers = _fetch_rows(
        "SELECT * FROM papers WHERE workspace_id = ?",
        (workspace_id,),
    )
    paper_ids = [paper["id"] for paper in papers]
    if paper_ids:
        placeholders = ",".join(["?"] * len(paper_ids))
        paper_tags = _fetch_rows(
            f"SELECT * FROM paper_tags WHERE paper_id IN ({placeholders})",
            tuple(paper_ids),
        )
    else:
        paper_tags = []

    assets = _fetch_rows(
        "SELECT * FROM assets WHERE workspace_id = ?",
        (workspace_id,),
    )
    asset_ids = [asset["id"] for asset in assets]
    if asset_ids and with_assets:
        placeholders = ",".join(["?"] * len(asset_ids))
        asset_versions = _fetch_rows(
            f"SELECT * FROM asset_versions WHERE asset_id IN ({placeholders})",
            tuple(asset_ids),
        )
    else:
        asset_versions = []

    coach_sessions = _fetch_rows(
        "SELECT * FROM coach_sessions WHERE workspace_id = ?",
        (workspace_id,),
    )
    ui_settings = _fetch_rows(
        "SELECT * FROM ui_settings WHERE workspace_id = ? OR workspace_id IS NULL",
        (workspace_id,),
    )
    ui_history = _fetch_rows(
        "SELECT * FROM ui_history WHERE workspace_id = ?",
        (workspace_id,),
    )

    concepts = _fetch_rows(
        "SELECT * FROM concept_cards WHERE workspace_id = ?",
        (workspace_id,),
    )
    concept_ids = [card["id"] for card in concepts]
    if concept_ids:
        placeholders = ",".join(["?"] * len(concept_ids))
        evidence = _fetch_rows(
            f"SELECT * FROM concept_evidence WHERE card_id IN ({placeholders})",
            tuple(concept_ids),
        )
    else:
        evidence = []

    marks = _fetch_rows(
        "SELECT * FROM document_processing_marks WHERE workspace_id = ?",
        (workspace_id,),
    )

    related_projects = _fetch_rows(
        "SELECT * FROM related_projects WHERE workspace_id = ?",
        (workspace_id,),
    )
    related_project_ids = [proj["id"] for proj in related_projects]
    if related_project_ids:
        placeholders = ",".join(["?"] * len(related_project_ids))
        related_sections = _fetch_rows(
            f"SELECT * FROM related_sections WHERE project_id IN ({placeholders})",
            tuple(related_project_ids),
        )
        related_candidates = _fetch_rows(
            f"SELECT * FROM related_candidates WHERE project_id IN ({placeholders})",
            tuple(related_project_ids),
        )
    else:
        related_sections = []
        related_candidates = []

    external_sources = _fetch_rows(
        "SELECT * FROM external_sources WHERE workspace_id = ?",
        (workspace_id,),
    )
    source_ids = [source["id"] for source in external_sources]
    if source_ids:
        placeholders = ",".join(["?"] * len(source_ids))
        external_mappings = _fetch_rows(
            f"SELECT * FROM external_mappings WHERE source_id IN ({placeholders})",
            tuple(source_ids),
        )
    else:
        external_mappings = []

    payload = sanitize_dict(
        {
            "documents": docs,
            "chunks": chunks,
            "document_pages": pages,
            "document_tags": tags,
            "courses": courses,
            "course_documents": course_docs,
            "papers": papers,
            "paper_tags": paper_tags,
            "assets": assets if with_assets else [],
            "asset_versions": asset_versions if with_assets else [],
            "coach_sessions": coach_sessions,
            "ui_settings": ui_settings,
            "ui_history": ui_history,
            "concept_cards": concepts,
            "concept_evidence": evidence,
            "document_processing_marks": marks,
            "related_projects": related_projects,
            "related_sections": related_sections,
            "related_candidates": related_candidates,
            "external_sources": external_sources,
            "external_mappings": external_mappings,
        }
    )

    counts = {key: len(value) for key, value in payload.items()}
    manifest = build_manifest(
        version="2.5.0",
        workspace_id=workspace_id,
        options={
            "with_pdf": with_pdf,
            "with_assets": with_assets,
            "with_prompts": with_prompts,
        },
        counts=counts,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "manifest.json").write_text(dump_manifest(manifest), encoding="utf-8")
        (root / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        if with_pdf:
            docs_dir = root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            for doc in docs:
                src = Path(doc["path"])
                if not src.exists():
                    continue
                target = docs_dir / f"{doc['id']}_{src.name}"
                shutil.copy2(src, target)

        if with_assets:
            assets_dir = root / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            for version in asset_versions:
                src = Path(version["content_path"])
                if not src.exists():
                    continue
                target = assets_dir / f"{version['id']}_{src.name}"
                shutil.copy2(src, target)

        if with_prompts:
            override = get_workspaces_dir() / workspace_id / "prompts_override.json"
            if override.exists():
                shutil.copy2(override, root / "prompts_override.json")

        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in root.rglob("*"):
                bundle.write(path, path.relative_to(root))
    return out_path
