from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from core.packs.manifest import build_manifest, dump_manifest
from infra.db import get_workspaces_dir
from service.asset_service import export_version_citations, list_assets_for_workspace, list_versions, read_version
from service.presentation_service import generate_slides


def _latest_slides_asset(workspace_id: str, doc_id: str) -> tuple[str, str] | None:
    assets = list_assets_for_workspace(workspace_id, kind="slides")
    for asset in assets:
        versions = list_versions(asset.id)
        if not versions:
            continue
        if asset.ref_id.startswith(f"{doc_id}:"):
            ordered = sorted(versions, key=lambda item: item.version_index, reverse=True)
            return asset.id, ordered[0].id
    return None


def build_slides_pack(
    *,
    workspace_id: str,
    doc_id: str,
    duration: str = "10",
    allow_generate: bool = True,
) -> Path:
    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "packs"
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"slides_pack_{doc_id}.zip"

    deck = ""
    qa = []
    asset_ref = _latest_slides_asset(workspace_id, doc_id)
    if not asset_ref and allow_generate:
        try:
            output = generate_slides(
                workspace_id=workspace_id,
                doc_id=doc_id,
                duration=duration,
                retrieval_mode="vector",
                save_outputs=True,
            )
            deck = output.deck
            qa = output.qa
            asset_ref = (output.asset_id, output.asset_version_id)
        except Exception:
            deck = "Slides generation skipped (LLM not configured)."
            qa = []
    elif asset_ref:
        view = read_version(asset_ref[0], asset_ref[1])
        deck = view.content

    citations_path = None
    if asset_ref:
        citations = export_version_citations(
            workspace_id=workspace_id,
            asset_id=asset_ref[0],
            version_id=asset_ref[1],
            formats=["json"],
        )
        citations_path = citations.get("json")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "deck.md").write_text(deck, encoding="utf-8")
        (root / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
        if citations_path and Path(citations_path).exists():
            (root / "citations.json").write_text(Path(citations_path).read_text(encoding="utf-8"), encoding="utf-8")
        else:
            (root / "citations.json").write_text("[]", encoding="utf-8")
        manifest = build_manifest(
            pack_type="slides",
            workspace_id=workspace_id,
            source_id=doc_id,
            items=["deck.md", "qa.json", "citations.json"],
        )
        (root / "manifest.json").write_text(dump_manifest(manifest), encoding="utf-8")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in root.iterdir():
                bundle.write(path, path.name)
    return zip_path
