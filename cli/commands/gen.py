from __future__ import annotations

import typer

from service.chat_service import ChatConfigError

from service.course_service import generate_overview, generate_cheatsheet
from service.paper_generate_service import generate_paper_card
from service.presentation_service import generate_slides


def gen(
    workspace: str = typer.Option(..., "--workspace"),
    type: str = typer.Option(..., "--type"),
    source: str = typer.Option(..., "--source"),
    duration: int = typer.Option(10, "--duration"),
    mode: str = typer.Option("vector", "--mode"),
) -> None:
    if type == "course_overview":
        try:
            output = generate_overview(workspace_id=workspace, course_id=source, retrieval_mode=mode)
            typer.echo(output.content)
            typer.echo(f"run_id: {output.run_id}")
        except ChatConfigError as exc:
            typer.echo(f"LLM not configured: {exc}")
        except Exception as exc:
            typer.echo(f"Generation failed: {exc}")
        return
    if type == "exam_cheatsheet":
        try:
            output = generate_cheatsheet(workspace_id=workspace, course_id=source, retrieval_mode=mode)
            typer.echo(output.content)
            typer.echo(f"run_id: {output.run_id}")
        except ChatConfigError as exc:
            typer.echo(f"LLM not configured: {exc}")
        except Exception as exc:
            typer.echo(f"Generation failed: {exc}")
        return
    if type == "paper_card":
        try:
            output = generate_paper_card(workspace_id=workspace, doc_id=source, retrieval_mode=mode)
            typer.echo(output.content)
            if output.warnings:
                typer.echo(f"warnings: {'; '.join(output.warnings)}")
            typer.echo(f"run_id: {output.run_id}")
        except ChatConfigError as exc:
            typer.echo(f"LLM not configured: {exc}")
        except Exception as exc:
            typer.echo(f"Generation failed: {exc}")
        return
    if type == "slides":
        try:
            output = generate_slides(
                workspace_id=workspace,
                doc_id=source,
                duration=str(duration),
                retrieval_mode=mode,
                save_outputs=False,
            )
            typer.echo(output.deck)
            if output.warnings:
                typer.echo(f"warnings: {'; '.join(output.warnings)}")
            typer.echo(f"run_id: {output.run_id}")
        except ChatConfigError as exc:
            typer.echo(f"LLM not configured: {exc}")
        except Exception as exc:
            typer.echo(f"Generation failed: {exc}")
        return

    raise typer.BadParameter("Unknown type.")
