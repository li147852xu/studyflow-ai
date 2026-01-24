from __future__ import annotations

import typer

from core.config.loader import load_config, apply_profile, ConfigError
from infra.models import init_db
from cli.commands.doctor import doctor
from cli.commands.workspace import workspace_app
from cli.commands.document import document_app
from cli.commands.index import index_app
from cli.commands.ingest import ingest
from cli.commands.query import query
from cli.commands.gen import gen
from cli.commands.asset import asset_app
from cli.commands.api import api_app
from cli.commands.coach import coach_app
from cli.commands.plugins import plugins_app
from cli.commands.import_cmd import import_app
from cli.commands.concepts_cmd import concepts_app
from cli.commands.related_cmd import related_app
from cli.commands.bundle_cmd import bundle_app
from cli.commands.pack_cmd import pack_app
from cli.commands.tasks_cmd import tasks_app
from cli.commands.clean_cmd import clean

app = typer.Typer(help="StudyFlow CLI")


@app.callback()
def _init_config() -> None:
    init_db()
    try:
        config = load_config()
        apply_profile(config)
    except ConfigError:
        pass


app.command()(doctor)
app.add_typer(workspace_app, name="workspace")
app.add_typer(document_app, name="document")
app.add_typer(index_app, name="index")
app.add_typer(asset_app, name="asset")
app.add_typer(api_app, name="api")
app.add_typer(coach_app, name="coach")
app.add_typer(plugins_app, name="plugins")
app.add_typer(import_app, name="import")
app.add_typer(concepts_app, name="concepts")
app.add_typer(related_app, name="related")
app.add_typer(bundle_app, name="bundle")
app.add_typer(pack_app, name="pack")
app.add_typer(tasks_app, name="tasks")
app.command()(ingest)
app.command()(query)
app.command()(gen)
app.command()(clean)

if __name__ == "__main__":
    app()
