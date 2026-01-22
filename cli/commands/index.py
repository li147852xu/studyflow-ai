from __future__ import annotations

import typer

from core.retrieval.bm25_index import build_bm25_index
from service.retrieval_service import build_or_refresh_index

index_app = typer.Typer(help="Index management")


@index_app.command("rebuild")
def rebuild(workspace_id: str) -> None:
    build_or_refresh_index(workspace_id=workspace_id, reset=True)
    build_bm25_index(workspace_id)
    typer.echo("rebuild ok")
