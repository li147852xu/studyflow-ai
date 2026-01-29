from __future__ import annotations

import os
import socket

import requests
import typer
import uvicorn

from backend.api import app

api_app = typer.Typer(help="API server commands")


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


@api_app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", help="Bind port"),
) -> None:
    if _is_port_open(host, port):
        typer.echo(f"Port {port} already in use.")
        raise typer.Exit(code=1)
    typer.echo(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


@api_app.command("ping")
def ping(
    base_url: str = typer.Option("http://127.0.0.1:8000", "--base-url"),
) -> None:
    token = os.getenv("API_TOKEN", "")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/health", headers=headers, timeout=5)
        if resp.status_code >= 400:
            typer.echo(f"API error {resp.status_code}: {resp.text}")
            raise typer.Exit(code=1)
        typer.echo(f"API ok: {resp.json()}")
    except requests.RequestException as exc:
        typer.echo(f"API ping failed: {exc}")
        raise typer.Exit(code=1)
