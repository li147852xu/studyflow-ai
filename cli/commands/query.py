from __future__ import annotations

import typer

from service.retrieval_service import answer_with_retrieval, retrieve_hits_mode, RetrievalError


def query(
    workspace: str = typer.Option(..., "--workspace"),
    mode: str = typer.Option("vector", "--mode"),
    question: str = typer.Argument(...),
) -> None:
    try:
        answer, hits, citations, run_id = answer_with_retrieval(
            workspace_id=workspace,
            query=question,
            mode=mode,
        )
        typer.echo(answer)
        typer.echo(f"run_id: {run_id}")
        for citation in citations:
            typer.echo(citation)
    except RetrievalError as exc:
        hits, used_mode = retrieve_hits_mode(
            workspace_id=workspace, query=question, mode=mode, top_k=8
        )
        typer.echo(f"Retrieval only ({used_mode}): {exc}")
        for hit in hits:
            typer.echo(f"{hit.chunk_id} p.{hit.page_start}-{hit.page_end}")
