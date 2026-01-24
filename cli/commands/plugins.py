from __future__ import annotations

import typer

from core.plugins.registry import load_builtin_plugins, list_plugins, get_plugin
from core.plugins.base import PluginContext


plugins_app = typer.Typer(help="Plugins management")


@plugins_app.command("ls")
def list_all() -> None:
    load_builtin_plugins()
    for plugin in list_plugins():
        typer.echo(f"{plugin.name} {plugin.version} {plugin.description}")


@plugins_app.command("run")
def run(
    name: str = typer.Argument(...),
    workspace: str = typer.Option(..., "--workspace"),
    path: str | None = typer.Option(None, "--path"),
    ocr_mode: str = typer.Option("off", "--ocr"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    load_builtin_plugins()
    plugin = get_plugin(name)
    context = PluginContext(
        workspace_id=workspace,
        args={
            "path": path,
            "ocr_mode": ocr_mode,
            "ocr_threshold": ocr_threshold,
        },
    )
    result = plugin.run(context)
    typer.echo(result.message)
