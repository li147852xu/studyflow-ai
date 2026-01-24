from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from infra.db import get_connection, get_workspaces_dir


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _asset_dir(workspace_id: str, asset_id: str) -> Path:
    return get_workspaces_dir() / workspace_id / "vault" / "assets" / asset_id


@dataclass
class AssetRecord:
    id: str
    workspace_id: str
    kind: str
    ref_id: str
    active_version_id: str | None
    created_at: str


@dataclass
class AssetVersionRecord:
    id: str
    asset_id: str
    version_index: int
    run_id: str | None
    model: str | None
    prompt_version: str | None
    content_path: str
    content_type: str
    citations_json: str | None
    hits_json: str | None
    created_at: str


def create_or_get_asset(*, workspace_id: str, kind: str, ref_id: str) -> AssetRecord:
    existing = get_asset_by_ref(workspace_id, kind, ref_id)
    if existing:
        return existing
    asset_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO assets (id, workspace_id, kind, ref_id, active_version_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (asset_id, workspace_id, kind, ref_id, None, _now_iso()),
        )
        connection.commit()
    return get_asset(asset_id)


def get_asset(asset_id: str) -> AssetRecord:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, kind, ref_id, active_version_id, created_at
            FROM assets
            WHERE id = ?
            """,
            (asset_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("Asset not found.")
    return AssetRecord(**dict(row))


def get_asset_by_ref(workspace_id: str, kind: str, ref_id: str) -> AssetRecord | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, workspace_id, kind, ref_id, active_version_id, created_at
            FROM assets
            WHERE workspace_id = ? AND kind = ? AND ref_id = ?
            """,
            (workspace_id, kind, ref_id),
        ).fetchone()
    return AssetRecord(**dict(row)) if row else None


def list_assets(workspace_id: str, kind: str | None = None) -> list[AssetRecord]:
    with get_connection() as connection:
        if kind:
            rows = connection.execute(
                """
                SELECT id, workspace_id, kind, ref_id, active_version_id, created_at
                FROM assets
                WHERE workspace_id = ? AND kind = ?
                ORDER BY created_at DESC
                """,
                (workspace_id, kind),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, workspace_id, kind, ref_id, active_version_id, created_at
                FROM assets
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                """,
                (workspace_id,),
            ).fetchall()
    return [AssetRecord(**dict(row)) for row in rows]


def list_asset_versions(asset_id: str) -> list[AssetVersionRecord]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, asset_id, version_index, run_id, model, prompt_version, content_path,
                   content_type, citations_json, hits_json, created_at
            FROM asset_versions
            WHERE asset_id = ?
            ORDER BY version_index DESC
            """,
            (asset_id,),
        ).fetchall()
    return [AssetVersionRecord(**dict(row)) for row in rows]


def read_asset_content(version: AssetVersionRecord) -> str:
    path = Path(version.content_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _next_version_index(asset_id: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT MAX(version_index) as max_idx FROM asset_versions WHERE asset_id = ?",
            (asset_id,),
        ).fetchone()
    max_idx = row["max_idx"] if row and row["max_idx"] is not None else 0
    return int(max_idx) + 1


def save_asset_version(
    *,
    workspace_id: str,
    asset_id: str,
    content: str,
    content_type: str,
    run_id: str | None = None,
    model: str | None = None,
    prompt_version: str | None = None,
    citations_json: str | None = None,
    hits_json: str | None = None,
) -> AssetVersionRecord:
    version_id = str(uuid.uuid4())
    version_index = _next_version_index(asset_id)
    asset_dir = _asset_dir(workspace_id, asset_id)
    asset_dir.mkdir(parents=True, exist_ok=True)
    ext = ".txt" if content_type != "markdown" else ".md"
    content_path = asset_dir / f"v{version_index}{ext}"
    content_path.write_text(content, encoding="utf-8")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO asset_versions (
                id, asset_id, version_index, run_id, model, prompt_version,
                content_path, content_type, citations_json, hits_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                asset_id,
                version_index,
                run_id,
                model,
                prompt_version,
                str(content_path),
                content_type,
                citations_json,
                hits_json,
                _now_iso(),
            ),
        )
        connection.execute(
            "UPDATE assets SET active_version_id = ? WHERE id = ?",
            (version_id, asset_id),
        )
        connection.commit()
    return AssetVersionRecord(
        id=version_id,
        asset_id=asset_id,
        version_index=version_index,
        run_id=run_id,
        model=model,
        prompt_version=prompt_version,
        content_path=str(content_path),
        content_type=content_type,
        citations_json=citations_json,
        hits_json=hits_json,
        created_at=_now_iso(),
    )


def set_active_version(asset_id: str, version_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE assets SET active_version_id = ? WHERE id = ?",
            (version_id, asset_id),
        )
        connection.commit()
