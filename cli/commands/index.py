from __future__ import annotations

import typer

from service.tasks_service import enqueue_index_task, run_task_by_id
from service.retrieval_service import index_status, vacuum_index

index_app = typer.Typer(help="Index management")


@index_app.command("rebuild")
def rebuild(workspace_id: str, doc_id: str | None = typer.Option(None, "--doc")) -> None:
    doc_ids = [doc_id] if doc_id else None
    task_id = enqueue_index_task(workspace_id=workspace_id, reset=doc_id is None, doc_ids=doc_ids)
    result = run_task_by_id(task_id)
    typer.echo(f"{task_id} indexed={result['indexed_count']} chunks")


@index_app.command("status")
def status(workspace_id: str) -> None:
    info = index_status(workspace_id)
    typer.echo(
        f"docs={info['doc_count']} chunks={info['chunk_count']} "
        f"vector={info['vector_count']} bm25={info['bm25_exists']} "
        f"orphans={info['orphan_chunks']}"
    )


@index_app.command("vacuum")
def vacuum(workspace_id: str) -> None:
    info = vacuum_index(workspace_id)
    typer.echo(
        f"vacuum ok docs={info['doc_count']} chunks={info['chunk_count']} "
        f"vector={info['vector_count']} orphans={info['orphan_chunks']}"
    )
