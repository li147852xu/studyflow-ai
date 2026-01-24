from __future__ import annotations

from pathlib import Path

import typer

from service.tasks_service import enqueue_ingest_task, run_task_by_id


def ingest(
    workspace: str = typer.Option(..., "--workspace"),
    pdf_path: str = typer.Argument(...),
    ocr: str = typer.Option("off", "--ocr", help="OCR mode: off|auto|on"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    path = Path(pdf_path)
    if not path.exists():
        raise typer.BadParameter("PDF path does not exist.")
    task_id = enqueue_ingest_task(
        workspace_id=workspace,
        path=str(path),
        ocr_mode=ocr,
        ocr_threshold=ocr_threshold,
    )
    result = run_task_by_id(task_id)
    typer.echo(f"{task_id} {result['doc_id']} {result['page_count']} pages")
