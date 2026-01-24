from __future__ import annotations

import typer

from core.assets.store import get_asset
from service.asset_service import (
    diff_versions,
    export_version_citations,
    list_assets_for_workspace,
    list_versions,
    read_version,
    set_active,
)

asset_app = typer.Typer(help="Manage generated assets")


@asset_app.command("ls")
def list_assets(
    workspace: str = typer.Option(..., "--workspace", help="Workspace id"),
    kind: str | None = typer.Option(None, "--kind", help="Filter by asset kind"),
) -> None:
    assets = list_assets_for_workspace(workspace, kind)
    if not assets:
        typer.echo("No assets found.")
        return
    for asset in assets:
        typer.echo(
            f"{asset.id} | {asset.kind} | {asset.ref_id} | active={asset.active_version_id or '-'}"
        )


@asset_app.command("show")
def show_asset(
    asset: str = typer.Option(..., "--asset", help="Asset id"),
    version: str | None = typer.Option(None, "--version", help="Version id"),
    active: bool = typer.Option(False, "--active", help="Show active version"),
) -> None:
    if not version and not active:
        raise typer.BadParameter("Provide --version or --active.")
    asset_record = get_asset(asset)
    version_id = asset_record.active_version_id if active else version
    if not version_id:
        raise typer.BadParameter("Active version not set.")
    view = read_version(asset, version_id)
    typer.echo(
        f"asset={asset_record.id} kind={asset_record.kind} ref={asset_record.ref_id} version={view.version.id}"
    )
    typer.echo(view.content)


@asset_app.command("pin")
def pin_asset(
    asset: str = typer.Option(..., "--asset", help="Asset id"),
    version: str = typer.Option(..., "--version", help="Version id"),
) -> None:
    set_active(asset, version)
    typer.echo("Active version updated.")


@asset_app.command("rollback")
def rollback_asset(
    asset: str = typer.Option(..., "--asset", help="Asset id"),
    version: str = typer.Option(..., "--version", help="Version id"),
) -> None:
    set_active(asset, version)
    typer.echo("Rolled back to selected version.")


@asset_app.command("diff")
def diff_asset(
    asset: str = typer.Option(..., "--asset", help="Asset id"),
    a: str = typer.Option(..., "--a", help="Version id A"),
    b: str = typer.Option(..., "--b", help="Version id B"),
) -> None:
    diff = diff_versions(asset, a, b)
    typer.echo(diff or "No differences.")


@asset_app.command("export-citations")
def export_citations_cmd(
    asset: str = typer.Option(..., "--asset", help="Asset id"),
    version: str = typer.Option(..., "--version", help="Version id"),
    formats: str = typer.Option("both", "--format", help="json|txt|both"),
) -> None:
    fmt_list = ["json", "txt"] if formats == "both" else [formats]
    paths = export_version_citations(
        workspace_id=get_asset(asset).workspace_id,
        asset_id=asset,
        version_id=version,
        formats=fmt_list,
    )
    for fmt, path in paths.items():
        typer.echo(f"{fmt}: {path}")
