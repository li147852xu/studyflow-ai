from __future__ import annotations

from pathlib import Path

import typer

from infra.db import get_workspaces_dir
from service.ingest_service import ingest_pdf


def ingest(
    workspace: str = typer.Option(..., "--workspace"),
    pdf_path: str = typer.Argument(...),
    ocr: str = typer.Option("off", "--ocr", help="OCR mode: off|auto|on"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    path = Path(pdf_path)
    if not path.exists():
        raise typer.BadParameter("PDF path does not exist.")
    data = path.read_bytes()
    result = ingest_pdf(
        workspace_id=workspace,
        filename=path.name,
        data=data,
        save_dir=get_workspaces_dir() / workspace / "uploads",
        ocr_mode=ocr,
        ocr_threshold=ocr_threshold,
    )
    typer.echo(f"{result.doc_id} {result.page_count} pages")
