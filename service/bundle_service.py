from __future__ import annotations

from pathlib import Path

from core.bundle.exporter import export_bundle
from core.bundle.importer import import_bundle
from infra.db import get_workspaces_dir


def bundle_export(
    *,
    workspace_id: str,
    out_path: str | None,
    with_pdf: bool,
    with_assets: bool,
    with_prompts: bool,
) -> str:
    if out_path:
        target = Path(out_path)
    else:
        target = get_workspaces_dir() / workspace_id / "exports" / f"bundle_{workspace_id}.zip"
    target = target.expanduser()
    return str(
        export_bundle(
            workspace_id=workspace_id,
            out_path=target,
            with_pdf=with_pdf,
            with_assets=with_assets,
            with_prompts=with_prompts,
        )
    )


def bundle_import(
    *,
    path: str,
    rebuild_index: bool,
) -> str:
    bundle_path = Path(path).expanduser()
    return import_bundle(bundle_path=bundle_path, rebuild_index=rebuild_index)
