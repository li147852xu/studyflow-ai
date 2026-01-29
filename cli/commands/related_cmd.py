from __future__ import annotations

import typer

from service.related_service import (
    RelatedServiceError,
    create_related_project,
    export_related_project,
    update_related_project,
)

related_app = typer.Typer(help="Related work manager commands")


@related_app.command("create")
def create(
    workspace: str = typer.Option(..., "--workspace"),
    papers: list[str] = typer.Option(..., "--papers"),
    topic: str = typer.Option(..., "--topic"),
    mode: str = typer.Option("vector", "--mode"),
) -> None:
    try:
        result = create_related_project(
            workspace_id=workspace,
            paper_ids=papers,
            topic=topic,
            retrieval_mode=mode,
        )
        typer.echo(result["draft"])
        typer.echo(f"project_id: {result['project_id']}")
    except RelatedServiceError as exc:
        typer.echo(str(exc))


@related_app.command("update")
def update(
    workspace: str = typer.Option(..., "--workspace"),
    project: str = typer.Option(..., "--project"),
    add_papers: list[str] = typer.Option(..., "--add-papers"),
    mode: str = typer.Option("vector", "--mode"),
) -> None:
    try:
        result = update_related_project(
            workspace_id=workspace,
            project_id=project,
            add_paper_ids=add_papers,
            retrieval_mode=mode,
        )
        typer.echo(result["draft"])
        if result["insert_suggestions"]:
            typer.echo("insert_suggestions:")
            for suggestion in result["insert_suggestions"]:
                typer.echo(f"- {suggestion}")
    except RelatedServiceError as exc:
        typer.echo(str(exc))


@related_app.command("export")
def export(
    workspace: str = typer.Option(..., "--workspace"),
    project: str = typer.Option(..., "--project"),
    format: str = typer.Option("txt", "--format"),
    out: str | None = typer.Option(None, "--out"),
) -> None:
    try:
        path = export_related_project(
            workspace_id=workspace,
            project_id=project,
            format=format,
            out_path=out,
        )
        typer.echo(path)
    except RelatedServiceError as exc:
        typer.echo(str(exc))
