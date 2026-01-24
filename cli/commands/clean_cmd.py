from __future__ import annotations

import shutil
from pathlib import Path

import typer

from infra.db import get_workspaces_dir


def _targets(workspace_id: str, what: list[str]) -> list[Path]:
    base = get_workspaces_dir() / workspace_id
    mapping = {
        "cache": base / "cache",
        "outputs": base / "outputs",
        "exports": base / "exports",
    }
    targets = []
    for key in what:
        if key in mapping:
            targets.append(mapping[key])
    return targets


def clean(
    workspace: str = typer.Option(..., "--workspace"),
    what: list[str] = typer.Option(["cache", "outputs", "exports"], "--what"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply"),
    yes: bool = typer.Option(False, "--yes"),
) -> None:
    targets = _targets(workspace, what)
    if not targets:
        typer.echo("No targets selected.")
        return
    for path in targets:
        typer.echo(f"{'[dry-run]' if dry_run or not yes else '[apply]'} {path}")
    if dry_run or not yes:
        typer.echo("Dry-run only. Use --apply --yes to delete.")
        return
    for path in targets:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    typer.echo("Clean complete.")
