from __future__ import annotations

import shutil

import typer

from infra.db import get_workspaces_dir
from service.workspace_service import (
    create_workspace,
    delete_workspace,
    list_workspaces,
    rename_workspace,
)

workspace_app = typer.Typer(help="Workspace management")


@workspace_app.command("ls")
def list_ws() -> None:
    for ws in list_workspaces():
        typer.echo(f"{ws['id']} {ws['name']} {ws['created_at']}")


@workspace_app.command("create")
def create(name: str) -> None:
    ws_id = create_workspace(name)
    typer.echo(ws_id)


@workspace_app.command("rename")
def rename(workspace_id: str, new_name: str) -> None:
    rename_workspace(workspace_id, new_name)
    typer.echo("ok")


@workspace_app.command("delete")
def delete(workspace_id: str, confirm: bool = typer.Option(False, "--confirm")) -> None:
    if not confirm:
        raise typer.BadParameter("Use --confirm to delete workspace.")
    delete_workspace(workspace_id)
    ws_dir = get_workspaces_dir() / workspace_id
    if ws_dir.exists():
        shutil.rmtree(ws_dir)
    typer.echo("deleted")
