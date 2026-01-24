from __future__ import annotations

import typer

from core.concepts.search import search_with_evidence
from service.concepts_service import build_concept_cards, ConceptsServiceError


concepts_app = typer.Typer(help="Concept cards commands")


@concepts_app.command("build")
def build(
    workspace: str = typer.Option(..., "--workspace"),
    papers: list[str] = typer.Option([], "--papers"),
    course: str | None = typer.Option(None, "--course"),
    incremental: bool = typer.Option(False, "--incremental"),
    mode: str = typer.Option("vector", "--mode"),
) -> None:
    try:
        result = build_concept_cards(
            workspace_id=workspace,
            retrieval_mode=mode,
            paper_ids=papers or None,
            course_id=course,
            incremental=incremental,
        )
        if result.get("skipped"):
            typer.echo("No new documents to process.")
            return
        typer.echo(f"cards_created: {result.get('cards_created', 0)}")
    except ConceptsServiceError as exc:
        typer.echo(str(exc))


@concepts_app.command("search")
def search(
    workspace: str = typer.Option(..., "--workspace"),
    query: str = typer.Argument(...),
    type_filter: str | None = typer.Option(None, "--type"),
) -> None:
    results = search_with_evidence(
        workspace_id=workspace,
        query=query,
        type_filter=type_filter,
    )
    if not results:
        typer.echo("No results.")
        return
    for item in results:
        card = item["card"]
        typer.echo(f"{card.name} [{card.type}]")
        typer.echo(card.content)
        for evidence in item["evidence"]:
            typer.echo(f"- {evidence}")
