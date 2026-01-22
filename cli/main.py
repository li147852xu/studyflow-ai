from __future__ import annotations

import typer

from core.config.loader import load_config, apply_profile, ConfigError
from cli.commands.doctor import doctor
from cli.commands.workspace import workspace_app
from cli.commands.document import document_app
from cli.commands.index import index_app
from cli.commands.ingest import ingest
from cli.commands.query import query
from cli.commands.gen import gen

app = typer.Typer(help="StudyFlow CLI")


@app.callback()
def _init_config() -> None:
    try:
        config = load_config()
        apply_profile(config)
    except ConfigError:
        pass


app.command()(doctor)
app.add_typer(workspace_app, name="workspace")
app.add_typer(document_app, name="document")
app.add_typer(index_app, name="index")
app.command()(ingest)
app.command()(query)
app.command()(gen)

if __name__ == "__main__":
    app()
