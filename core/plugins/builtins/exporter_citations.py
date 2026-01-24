from __future__ import annotations

from core.plugins.base import PluginBase, PluginContext, PluginResult
from service.asset_service import export_version_citations, list_assets_for_workspace, list_versions


class ExportCitationsPlugin(PluginBase):
    name = "exporter_citations"
    version = "1.0.0"
    description = "Export citations for active asset versions."

    def run(self, context: PluginContext) -> PluginResult:
        formats = context.args.get("formats", ["json", "txt"])
        assets = list_assets_for_workspace(context.workspace_id)
        if not assets:
            return PluginResult(ok=False, message="No assets found.")
        count = 0
        for asset in assets:
            versions = list_versions(asset.id)
            active_id = asset.active_version_id or (versions[0].id if versions else None)
            if not active_id:
                continue
            export_version_citations(
                workspace_id=context.workspace_id,
                asset_id=asset.id,
                version_id=active_id,
                formats=formats,
            )
            count += 1
        return PluginResult(ok=True, message=f"Exported citations for {count} assets.")
