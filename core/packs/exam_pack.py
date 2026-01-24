from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from core.packs.manifest import build_manifest, dump_manifest
from service.asset_service import export_version_citations, get_asset_by_ref, list_versions, read_version
from infra.db import get_workspaces_dir


def build_exam_pack(
    *,
    workspace_id: str,
    course_id: str,
) -> Path:
    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "packs"
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"exam_pack_{course_id}.zip"

    asset = get_asset_by_ref(workspace_id, "course_cheatsheet", course_id)
    if not asset:
        raise RuntimeError("No cheatsheet asset found for course.")
    versions = list_versions(asset.id)
    if not versions:
        raise RuntimeError("No cheatsheet versions found for course.")
    ordered = sorted(versions, key=lambda item: item.version_index, reverse=True)
    view = read_version(asset.id, ordered[0].id)

    checklist = []
    for line in view.content.splitlines():
        line = line.strip()
        if line and line.startswith("-"):
            checklist.append(line.lstrip("- ").strip())
        if len(checklist) >= 10:
            break

    citations = export_version_citations(
        workspace_id=workspace_id,
        asset_id=asset.id,
        version_id=ordered[0].id,
        formats=["json"],
    )
    citations_path = citations.get("json")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "cheatsheet.txt").write_text(view.content, encoding="utf-8")
        (root / "checklist.json").write_text(json.dumps(checklist, ensure_ascii=False, indent=2), encoding="utf-8")
        if citations_path and Path(citations_path).exists():
            (root / "citations.json").write_text(Path(citations_path).read_text(encoding="utf-8"), encoding="utf-8")
        else:
            (root / "citations.json").write_text("[]", encoding="utf-8")
        manifest = build_manifest(
            pack_type="exam",
            workspace_id=workspace_id,
            source_id=course_id,
            items=["cheatsheet.txt", "checklist.json", "citations.json"],
        )
        (root / "manifest.json").write_text(dump_manifest(manifest), encoding="utf-8")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in root.iterdir():
                bundle.write(path, path.name)
    return zip_path
