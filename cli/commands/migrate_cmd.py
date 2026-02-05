from __future__ import annotations

import typer

from core.storage.migrations import run_migrations


def migrate() -> None:
    version = run_migrations()
    typer.echo(f"Schema migrated to v{version}")

