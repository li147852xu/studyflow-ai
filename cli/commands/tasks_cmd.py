from __future__ import annotations

import typer

from service.tasks_service import (
    cancel_task_by_id,
    get_task_by_id,
    list_tasks_for_workspace,
    resume_task_by_id,
    retry_task_by_id,
)

tasks_app = typer.Typer(help="Task queue commands")


@tasks_app.command("ls")
def list_tasks(
    workspace: str | None = typer.Option(None, "--workspace"),
    status: str | None = typer.Option(None, "--status"),
) -> None:
    tasks = list_tasks_for_workspace(workspace_id=workspace, status=status)
    for task in tasks:
        typer.echo(f"{task.id} {task.type} {task.status} {task.progress or 0}")


@tasks_app.command("show")
def show(task_id: str) -> None:
    task = get_task_by_id(task_id)
    if not task:
        typer.echo("Task not found.")
        return
    typer.echo(
        f"{task.id} {task.type} {task.status} {task.progress or 0} {task.error or ''}"
    )


@tasks_app.command("cancel")
def cancel(task_id: str) -> None:
    cancel_task_by_id(task_id)
    typer.echo("cancelled")


@tasks_app.command("retry")
def retry(task_id: str) -> None:
    result = retry_task_by_id(task_id)
    typer.echo(f"retried {result}")


@tasks_app.command("resume")
def resume(task_id: str) -> None:
    result = resume_task_by_id(task_id)
    typer.echo(f"resumed {result}")
