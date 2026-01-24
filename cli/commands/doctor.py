from __future__ import annotations

import os
import sys
import socket
import shutil
from urllib.parse import urlparse

import typer

from core.config.loader import load_config, apply_profile, ConfigError


def doctor() -> None:
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
