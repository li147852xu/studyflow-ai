from __future__ import annotations

import typer

from core.plugins.base import PluginContext
from core.plugins.registry import get_plugin, load_builtin_plugins

import_app = typer.Typer(help="External import commands")


def _run_plugin(name: str, workspace: str, args: dict) -> None:
    load_builtin_plugins()
    plugin = get_plugin(name)
    result = plugin.run(PluginContext(workspace_id=workspace, args=args))
    typer.echo(result.message)


@import_app.command("zotero")
def import_zotero(
    workspace: str = typer.Option(..., "--workspace"),
    data_dir: str = typer.Option(..., "--data-dir"),
    copy: bool = typer.Option(True, "--copy/--symlink"),
    ocr: str = typer.Option("off", "--ocr"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    _run_plugin(
        "importer_zotero",
        workspace,
        {
            "data_dir": data_dir,
            "copy": copy,
            "ocr_mode": ocr,
            "ocr_threshold": ocr_threshold,
        },
    )


@import_app.command("arxiv")
def import_arxiv(
    workspace: str = typer.Option(..., "--workspace"),
    arxiv_id: str = typer.Option(..., "--id"),
    ocr: str = typer.Option("off", "--ocr"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    _run_plugin(
        "importer_arxiv",
        workspace,
        {
            "arxiv_id": arxiv_id,
            "ocr_mode": ocr,
            "ocr_threshold": ocr_threshold,
        },
    )


@import_app.command("doi")
def import_doi(
    workspace: str = typer.Option(..., "--workspace"),
    doi: str = typer.Option(..., "--doi"),
    ocr: str = typer.Option("off", "--ocr"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    _run_plugin(
        "importer_doi",
        workspace,
        {
            "doi": doi,
            "ocr_mode": ocr,
            "ocr_threshold": ocr_threshold,
        },
    )


@import_app.command("url")
def import_url(
    workspace: str = typer.Option(..., "--workspace"),
    url: str = typer.Option(..., "--url"),
    ocr: str = typer.Option("off", "--ocr"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    _run_plugin(
        "importer_url",
        workspace,
        {
            "url": url,
            "ocr_mode": ocr,
            "ocr_threshold": ocr_threshold,
        },
    )


@import_app.command("folder")
def import_folder(
    workspace: str = typer.Option(..., "--workspace"),
    path: str = typer.Option(..., "--path"),
    copy: bool = typer.Option(True, "--copy/--symlink"),
    ignore: list[str] = typer.Option([], "--ignore"),
    ocr: str = typer.Option("off", "--ocr"),
    ocr_threshold: int = typer.Option(50, "--ocr-threshold"),
) -> None:
    _run_plugin(
        "importer_folder_sync",
        workspace,
        {
            "path": path,
            "copy": copy,
            "ignore": ignore,
            "ocr_mode": ocr,
            "ocr_threshold": ocr_threshold,
        },
    )
