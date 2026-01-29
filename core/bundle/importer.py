from __future__ import annotations

import json
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from core.retrieval.bm25_index import build_bm25_index
from infra.db import get_connection, get_workspaces_dir
from service.retrieval_service import build_or_refresh_index
from service.workspace_service import create_workspace


def _insert_rows(table: str, rows: list[dict]) -> None:
    if not rows:
        return
    columns = list(rows[0].keys())
    placeholders = ",".join(["?"] * len(columns))
    values = [tuple(row.get(col) for col in columns) for row in rows]
    with get_connection() as connection:
        connection.executemany(
            f"INSERT OR IGNORE INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
            values,
        )
        connection.commit()


def import_bundle(
    *,
    bundle_path: Path,
    rebuild_index: bool = False,
) -> str:
    if not bundle_path.exists():
        raise RuntimeError("Bundle path not found.")
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        with zipfile.ZipFile(bundle_path, "r") as bundle:
            bundle.extractall(root)

        data = json.loads((root / "data.json").read_text(encoding="utf-8"))
        original_workspace_id = json.loads((root / "manifest.json").read_text(encoding="utf-8")).get(
            "workspace_id"
        )
        new_workspace_id = create_workspace(f"imported_{original_workspace_id}")

        docs_dir = get_workspaces_dir() / new_workspace_id / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Remap workspace_id for workspace-scoped tables
        for key in [
            "documents",
            "courses",
            "papers",
            "assets",
            "coach_sessions",
            "ui_settings",
            "ui_history",
            "concept_cards",
            "document_processing_marks",
            "related_projects",
            "external_sources",
        ]:
            for row in data.get(key, []):
                row["workspace_id"] = new_workspace_id

        def remap_ids(rows: list[dict]) -> dict[str, str]:
            mapping: dict[str, str] = {}
            for row in rows:
                old = row.get("id")
                new_id = str(uuid.uuid4())
                row["id"] = new_id
                if old:
                    mapping[old] = new_id
            return mapping

        course_map = remap_ids(data.get("courses", []))
        paper_map = remap_ids(data.get("papers", []))
        asset_map = remap_ids(data.get("assets", []))
        card_map = remap_ids(data.get("concept_cards", []))
        project_map = remap_ids(data.get("related_projects", []))
        source_map = remap_ids(data.get("external_sources", []))

        # Remap documents separately to preserve bundle doc mapping
        doc_rows = data.get("documents", [])
        doc_id_map: dict[str, str] = {}
        for row in doc_rows:
            old = row["id"]
            new_id = str(uuid.uuid4())
            row["id"] = new_id
            doc_id_map[old] = new_id

        # Copy PDFs if present
        docs_in_bundle = list((root / "docs").glob("*")) if (root / "docs").exists() else []
        doc_file_map = {Path(path).stem.split("_", 1)[0]: path for path in docs_in_bundle}
        for doc in data.get("documents", []):
            original_id = next((key for key, val in doc_id_map.items() if val == doc["id"]), None)
            src = doc_file_map.get(original_id or "")
            filename = Path(doc.get("path", "")).name or f"{doc['id']}.pdf"
            target = docs_dir / filename
            if src:
                shutil.copy2(src, target)
            doc["path"] = str(target)

        # Assets if present
        assets_dir = get_workspaces_dir() / new_workspace_id / "vault" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        asset_file_map = {}
        for path in (root / "assets").glob("*") if (root / "assets").exists() else []:
            key = Path(path).stem.split("_", 1)[0]
            asset_file_map[key] = path
        for version in data.get("asset_versions", []):
            src = asset_file_map.get(version["id"])
            filename = Path(version.get("content_path", "")).name or f"{version['id']}.txt"
            target = assets_dir / filename
            if src:
                shutil.copy2(src, target)
            version["content_path"] = str(target)

        # Remap IDs and foreign keys
        for row in data.get("documents", []):
            row["id"] = row["id"]

        for row in data.get("chunks", []):
            old_doc = row["doc_id"]
            row["doc_id"] = doc_id_map.get(old_doc, old_doc)
            row["id"] = f"{row['doc_id']}:{row['chunk_index']}"

        for row in data.get("document_pages", []):
            old_doc = row["doc_id"]
            row["doc_id"] = doc_id_map.get(old_doc, old_doc)
            row["id"] = f"{row['doc_id']}:{row['page_number']}"

        for row in data.get("document_tags", []):
            row["id"] = str(uuid.uuid4())
            row["doc_id"] = doc_id_map.get(row["doc_id"], row["doc_id"])

        for row in data.get("course_documents", []):
            row["id"] = str(uuid.uuid4())
            row["course_id"] = course_map.get(row["course_id"], row["course_id"])
            row["doc_id"] = doc_id_map.get(row["doc_id"], row["doc_id"])

        for row in data.get("papers", []):
            old_doc = row["doc_id"]
            row["doc_id"] = doc_id_map.get(old_doc, old_doc)
            row["id"] = paper_map.get(row["id"], row["id"])

        for row in data.get("paper_tags", []):
            row["id"] = str(uuid.uuid4())
            row["paper_id"] = paper_map.get(row["paper_id"], row["paper_id"])

        for row in data.get("assets", []):
            row["id"] = asset_map.get(row["id"], row["id"])

        for row in data.get("asset_versions", []):
            row["id"] = str(uuid.uuid4())
            row["asset_id"] = asset_map.get(row["asset_id"], row["asset_id"])

        for row in data.get("coach_sessions", []):
            row["id"] = str(uuid.uuid4())

        for row in data.get("ui_settings", []):
            row["id"] = str(uuid.uuid4())

        for row in data.get("ui_history", []):
            row["id"] = str(uuid.uuid4())

        for row in data.get("concept_cards", []):
            row["id"] = card_map.get(row["id"], row["id"])

        for row in data.get("concept_evidence", []):
            old_doc = row["doc_id"]
            row["id"] = str(uuid.uuid4())
            row["card_id"] = card_map.get(row["card_id"], row["card_id"])
            row["doc_id"] = doc_id_map.get(old_doc, old_doc)
            row["chunk_id"] = row["chunk_id"].replace(
                row["chunk_id"].split(":")[0],
                doc_id_map.get(old_doc, old_doc),
            )

        for row in data.get("document_processing_marks", []):
            row["id"] = str(uuid.uuid4())
            row["doc_id"] = doc_id_map.get(row["doc_id"], row["doc_id"])

        for row in data.get("related_projects", []):
            row["id"] = project_map.get(row["id"], row["id"])

        section_id_map: dict[str, str] = {}
        for row in data.get("related_sections", []):
            old_section = row["id"]
            row["id"] = str(uuid.uuid4())
            section_id_map[old_section] = row["id"]
            row["project_id"] = project_map.get(row["project_id"], row["project_id"])
        for row in data.get("related_candidates", []):
            row["id"] = str(uuid.uuid4())
            row["project_id"] = project_map.get(row["project_id"], row["project_id"])
            row["section_id"] = section_id_map.get(row["section_id"], row["section_id"])
            row["paper_id"] = paper_map.get(row["paper_id"], row["paper_id"])

        for row in data.get("external_sources", []):
            row["id"] = source_map.get(row["id"], row["id"])

        for row in data.get("external_mappings", []):
            row["id"] = str(uuid.uuid4())
            row["source_id"] = source_map.get(row["source_id"], row["source_id"])
            if row.get("doc_id"):
                row["doc_id"] = doc_id_map.get(row["doc_id"], row["doc_id"])

        # Prompts override
        if (root / "prompts_override.json").exists():
            dest = get_workspaces_dir() / new_workspace_id / "prompts_override.json"
            shutil.copy2(root / "prompts_override.json", dest)

        # Insert rows in dependency order
        _insert_rows("documents", data.get("documents", []))
        _insert_rows("chunks", data.get("chunks", []))
        _insert_rows("document_pages", data.get("document_pages", []))
        _insert_rows("document_tags", data.get("document_tags", []))
        _insert_rows("courses", data.get("courses", []))
        _insert_rows("course_documents", data.get("course_documents", []))
        _insert_rows("papers", data.get("papers", []))
        _insert_rows("paper_tags", data.get("paper_tags", []))
        _insert_rows("assets", data.get("assets", []))
        _insert_rows("asset_versions", data.get("asset_versions", []))
        _insert_rows("coach_sessions", data.get("coach_sessions", []))
        _insert_rows("ui_settings", data.get("ui_settings", []))
        _insert_rows("ui_history", data.get("ui_history", []))
        _insert_rows("concept_cards", data.get("concept_cards", []))
        _insert_rows("concept_evidence", data.get("concept_evidence", []))
        _insert_rows("document_processing_marks", data.get("document_processing_marks", []))
        _insert_rows("related_projects", data.get("related_projects", []))
        _insert_rows("related_sections", data.get("related_sections", []))
        _insert_rows("related_candidates", data.get("related_candidates", []))
        _insert_rows("external_sources", data.get("external_sources", []))
        _insert_rows("external_mappings", data.get("external_mappings", []))

        if rebuild_index:
            try:
                build_or_refresh_index(workspace_id=new_workspace_id, reset=True)
            except Exception:
                pass
            try:
                build_bm25_index(new_workspace_id)
            except Exception:
                pass

    return new_workspace_id
