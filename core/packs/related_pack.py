from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from core.assets import get_asset_by_ref
from core.concepts.store import list_cards, list_evidence
from core.packs.manifest import build_manifest, dump_manifest
from core.related.store import get_project, list_sections
from infra.db import get_workspaces_dir
from service.asset_service import export_version_citations, list_versions, read_version


def build_related_pack(
    *,
    workspace_id: str,
    project_id: str,
) -> Path:
    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "packs"
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"related_pack_{project_id}.zip"

    project = get_project(project_id)
    sections = list_sections(project_id)
    asset = get_asset_by_ref(workspace_id, "related_work", project_id)
    draft = project.current_draft or ""

    citations_path = None
    if asset:
        versions = list_versions(asset.id)
        ordered = sorted(versions, key=lambda item: item.version_index, reverse=True)
        if ordered:
            view = read_version(asset.id, ordered[0].id)
            draft = view.content
            citations = export_version_citations(
                workspace_id=workspace_id,
                asset_id=asset.id,
                version_id=ordered[0].id,
                formats=["json"],
            )
            citations_path = citations.get("json")

    concept_snapshot = []
    for card in list_cards(workspace_id):
        evidence = list_evidence(card.id)
        concept_snapshot.append(
            {
                "id": card.id,
                "name": card.name,
                "type": card.type,
                "content": card.content,
                "evidence_count": len(evidence),
            }
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        outline_payload = [
            {
                "title": section.title,
                "bullets": json.loads(section.bullets_json or "[]"),
            }
            for section in sections
        ]
        (root / "outline.json").write_text(json.dumps(outline_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (root / "draft.txt").write_text(draft, encoding="utf-8")
        (root / "concepts.json").write_text(
            json.dumps(concept_snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if citations_path and Path(citations_path).exists():
            (root / "citations.json").write_text(Path(citations_path).read_text(encoding="utf-8"), encoding="utf-8")
        else:
            (root / "citations.json").write_text("[]", encoding="utf-8")
        manifest = build_manifest(
            pack_type="related",
            workspace_id=workspace_id,
            source_id=project_id,
            items=["outline.json", "draft.txt", "citations.json", "concepts.json"],
        )
        (root / "manifest.json").write_text(dump_manifest(manifest), encoding="utf-8")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in root.iterdir():
                bundle.write(path, path.name)
    return zip_path
