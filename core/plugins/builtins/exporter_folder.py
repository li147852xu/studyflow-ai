from __future__ import annotations

from pathlib import Path

from core.plugins.base import PluginBase, PluginContext, PluginResult
from infra.db import get_workspaces_dir
from service.asset_service import list_assets_for_workspace, list_versions, read_version


class ExportFolderPlugin(PluginBase):
    name = "exporter_folder"
    version = "1.0.0"
    description = "Export active asset versions to a folder."

    def run(self, context: PluginContext) -> PluginResult:
        target = context.args.get("path")
        output_dir = (
            Path(target)
            if target
            else get_workspaces_dir() / context.workspace_id / "outputs" / "exports"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        assets = list_assets_for_workspace(context.workspace_id)
        if not assets:
            return PluginResult(ok=False, message="No assets found.")
        count = 0
        for asset in assets:
            versions = list_versions(asset.id)
            active_id = asset.active_version_id or (versions[0].id if versions else None)
            if not active_id:
                continue
            view = read_version(asset.id, active_id)
            ext = "md" if view.version.content_type == "markdown" else "txt"
            target_path = output_dir / f"{asset.kind}_{asset.ref_id}_{view.version.id}.{ext}"
            target_path.write_text(view.content, encoding="utf-8")
            count += 1
        return PluginResult(ok=True, message=f"Exported {count} assets.", data={"count": count})
