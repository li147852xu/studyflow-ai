from __future__ import annotations

import typer

from infra.db import get_connection
from service.document_service import delete_document_by_id, list_documents

document_app = typer.Typer(help="Document management")


@document_app.command("ls")
def list_docs(workspace_id: str) -> None:
    for doc in list_documents(workspace_id):
        typer.echo(f"{doc['id']} {doc['filename']} {doc['path']}")


@document_app.command("info")
def info(doc_id: str) -> None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, filename, path, page_count, sha256, updated_at
            FROM documents
            WHERE id = ?
            """,
            (doc_id,),
        ).fetchone()
    if not row:
        raise typer.BadParameter("Document not found.")
    typer.echo(dict(row))


@document_app.command("delete")
def delete(doc_id: str, workspace_id: str) -> None:
    delete_document_by_id(workspace_id, doc_id)
    typer.echo("deleted")
