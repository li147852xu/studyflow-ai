from __future__ import annotations

import typer

from service.coach_service import (
    clear_coach_sessions,
    list_coach_sessions,
    show_coach_session,
    start_coach,
    submit_coach,
)


coach_app = typer.Typer(help="Study coach commands")


@coach_app.command("start")
def start(
    workspace: str = typer.Option(..., "--workspace"),
    problem: str = typer.Option(..., "--problem"),
    mode: str = typer.Option("vector", "--mode"),
) -> None:
    result = start_coach(workspace_id=workspace, problem=problem, retrieval_mode=mode)
    typer.echo(result.output.content)
    typer.echo(f"session_id: {result.session.id}")


@coach_app.command("submit")
def submit(
    workspace: str = typer.Option(..., "--workspace"),
    session: str = typer.Option(..., "--session"),
    answer: str = typer.Option(..., "--answer"),
    mode: str = typer.Option("vector", "--mode"),
) -> None:
    result = submit_coach(
        workspace_id=workspace,
        session_id=session,
        answer=answer,
        retrieval_mode=mode,
    )
    typer.echo(result.output.content)


@coach_app.command("ls")
def list_sessions(workspace: str = typer.Option(..., "--workspace")) -> None:
    sessions = list_coach_sessions(workspace)
    if not sessions:
        typer.echo("No sessions.")
        return
    for session in sessions:
        typer.echo(f"{session.id} {session.status} {session.problem[:60]}")


@coach_app.command("show")
def show(session: str = typer.Option(..., "--session")) -> None:
    data = show_coach_session(session)
    typer.echo(f"problem: {data.problem}")
    if data.phase_a_output:
        typer.echo("phase_a:")
        typer.echo(data.phase_a_output)
    if data.phase_b_output:
        typer.echo("phase_b:")
        typer.echo(data.phase_b_output)


@coach_app.command("clear")
def clear(workspace: str = typer.Option(..., "--workspace")) -> None:
    clear_coach_sessions(workspace)
    typer.echo("cleared")
