from __future__ import annotations

import os
import sys
import socket
import shutil
from urllib.parse import urlparse

import typer

from core.config.loader import load_config, apply_profile, ConfigError
from infra.db import get_connection, get_workspaces_dir
from service.retrieval_service import index_status
from service.workspace_service import list_workspaces


def _dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (os.path.getsize(os.path.join(root, name)) or 0)
            except OSError:
                continue
    return total


def doctor(
    deep: bool = typer.Option(False, "--deep"),
    workspace: str | None = typer.Option(None, "--workspace"),
) -> None:
    typer.echo(f"Python: {sys.version.split()[0]}")
    try:
        config = load_config()
        apply_profile(config)
        typer.echo(f"Config profile: {config.profile}")
    except ConfigError as exc:
        typer.echo(f"Config: {exc}")

    llm_key = bool(os.getenv("STUDYFLOW_LLM_API_KEY"))
    embed_model = os.getenv("STUDYFLOW_EMBED_MODEL", "")
    typer.echo(f"LLM key configured: {'yes' if llm_key else 'no'}")
    typer.echo(f"Embedding model: {embed_model or 'not set'}")
    api_token = bool(os.getenv("API_TOKEN"))
    typer.echo(f"API token configured: {'yes' if api_token else 'no'}")
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401

        typer.echo("FastAPI/uvicorn: available")
    except Exception:
        typer.echo("FastAPI/uvicorn: missing (install dependencies)")

    base_url = os.getenv("STUDYFLOW_API_BASE_URL", "http://127.0.0.1:8000")
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        in_use = sock.connect_ex((host, port)) == 0
    typer.echo(f"API port {host}:{port} in use: {'yes' if in_use else 'no'}")

    try:
        from core.ingest.ocr import OCRSettings, ocr_available
        ok, reason = ocr_available(OCRSettings())
        tesseract_path = shutil.which("tesseract")
        typer.echo(f"OCR available: {'yes' if ok else 'no'}")
        if not ok:
            typer.echo(f"OCR reason: {reason}")
            typer.echo("Install tesseract:")
            typer.echo("  macOS: brew install tesseract")
            typer.echo("  Ubuntu: sudo apt-get install tesseract-ocr")
            typer.echo("  Windows: choco install tesseract")
        else:
            typer.echo(f"Tesseract path: {tesseract_path or 'not found'}")
    except Exception as exc:
        typer.echo(f"OCR check failed: {exc}")

    try:
        import requests  # noqa: F401

        typer.echo("Download support: available (arXiv/DOI/URL imports)")
    except Exception:
        typer.echo("Download support: missing (install requests)")

    if not deep:
        return

    workspaces = (
        [workspace]
        if workspace
        else [item["id"] for item in list_workspaces()]
    )
    if not workspaces:
        typer.echo("No workspaces found for deep scan.")
        return
    for workspace_id in workspaces:
        typer.echo(f"Deep scan: {workspace_id}")
        status = index_status(workspace_id)
        typer.echo(
            f"  docs={status['doc_count']} chunks={status['chunk_count']} "
            f"orphans={status['orphan_chunks']} vector={status['vector_count']} bm25={status['bm25_exists']}"
        )
        with get_connection() as connection:
            dup_rows = connection.execute(
                """
                SELECT sha256, COUNT(*) as count
                FROM documents
                WHERE workspace_id = ? AND sha256 IS NOT NULL
                GROUP BY sha256
                HAVING COUNT(*) > 1
                """,
                (workspace_id,),
            ).fetchall()
        if dup_rows:
            typer.echo(f"  duplicate docs: {len(dup_rows)}")
        else:
            typer.echo("  duplicate docs: 0")
        workspace_dir = get_workspaces_dir() / workspace_id
        size_bytes = _dir_size(str(workspace_dir))
        typer.echo(f"  disk usage: {size_bytes} bytes")
        cache_path = workspace_dir / "cache" / "embeddings.sqlite"
        if cache_path.exists():
            try:
                import sqlite3

                conn = sqlite3.connect(cache_path)
                row = conn.execute(
                    "SELECT COUNT(*) as count FROM embeddings_cache"
                ).fetchone()
                conn.close()
                typer.echo(f"  embedding cache: {row[0]} entries")
            except Exception:
                typer.echo("  embedding cache: unreadable")
        else:
            typer.echo("  embedding cache: missing")
