from __future__ import annotations

import os
import sys

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
