from __future__ import annotations

import typer

from service.bundle_service import bundle_export, bundle_import


bundle_app = typer.Typer(help="Workspace bundle commands")


@bundle_app.command("export")
def export(
    workspace: str = typer.Option(..., "--workspace"),
    out: str | None = typer.Option(None, "--out"),
    with_pdf: bool = typer.Option(False, "--with-pdf"),
    with_assets: bool = typer.Option(False, "--with-assets"),
    with_prompts: bool = typer.Option(False, "--with-prompts"),
) -> None:
    path = bundle_export(
        workspace_id=workspace,
        out_path=out,
        with_pdf=with_pdf,
        with_assets=with_assets,
        with_prompts=with_prompts,
    )
    typer.echo(path)


@bundle_app.command("import")
def import_bundle_cmd(
    path: str = typer.Option(..., "--path"),
    rebuild_index: bool = typer.Option(False, "--rebuild-index"),
) -> None:
    workspace_id = bundle_import(path=path, rebuild_index=rebuild_index)
    typer.echo(workspace_id)
