from __future__ import annotations

import typer

from service.pack_service import PackServiceError, make_pack

pack_app = typer.Typer(help="Submission pack commands")


@pack_app.command("make")
def make(
    workspace: str = typer.Option(..., "--workspace"),
    pack_type: str = typer.Option(..., "--type"),
    source: str = typer.Option(..., "--source"),
) -> None:
    try:
        path = make_pack(workspace_id=workspace, pack_type=pack_type, source_id=source)
        typer.echo(path)
    except PackServiceError as exc:
        typer.echo(str(exc))
