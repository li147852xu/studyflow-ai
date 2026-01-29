from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from core.assets.citations import export_citations, format_citations_payload
from core.assets.diff import diff_text
from core.assets.store import (
    AssetRecord,
    AssetVersionRecord,
    create_or_get_asset,
    get_asset,
    list_asset_versions,
    list_assets,
    read_asset_content,
    save_asset_version,
    set_active_version,
)
from core.retrieval.retriever import Hit


def _hash_ref(text: str) -> str:
    digest = hashlib.sha256()
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()[:10]


def _hits_to_json(hits: list[Hit]) -> str:
    payload = [
        {
            "chunk_id": hit.chunk_id,
            "filename": hit.filename,
            "page_start": hit.page_start,
            "page_end": hit.page_end,
            "text": hit.text,
            "score": hit.score,
        }
        for hit in hits
    ]
    return json.dumps(payload, ensure_ascii=False)


@dataclass
class AssetVersionView:
    asset: AssetRecord
    version: AssetVersionRecord
    content: str


def create_asset_version(
    *,
    workspace_id: str,
    kind: str,
    ref_id: str,
    content: str,
    content_type: str,
    run_id: str | None,
    model: str | None,
    provider: str | None,
    temperature: float | None,
    max_tokens: int | None,
    retrieval_mode: str | None,
    embed_model: str | None,
    seed: int | None,
    prompt_version: str,
    hits: list[Hit],
) -> AssetVersionRecord:
    asset = create_or_get_asset(workspace_id=workspace_id, kind=kind, ref_id=ref_id)
    hits_json = _hits_to_json(hits) if hits else None
    citations_json = None
    if hits_json:
        citations_json = json.dumps(format_citations_payload(hits_json), ensure_ascii=False)
    return save_asset_version(
        workspace_id=workspace_id,
        asset_id=asset.id,
        content=content,
        content_type=content_type,
        run_id=run_id,
        model=model,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
        retrieval_mode=retrieval_mode,
        embed_model=embed_model,
        seed=seed,
        prompt_version=prompt_version,
        citations_json=citations_json,
        hits_json=hits_json,
    )


def list_assets_for_workspace(workspace_id: str, kind: str | None = None) -> list[AssetRecord]:
    return list_assets(workspace_id, kind)


def list_versions(asset_id: str) -> list[AssetVersionRecord]:
    return list_asset_versions(asset_id)


def read_version(asset_id: str, version_id: str) -> AssetVersionView:
    asset = get_asset(asset_id)
    versions = list_asset_versions(asset_id)
    version = next((v for v in versions if v.id == version_id), None)
    if not version:
        raise RuntimeError("Asset version not found.")
    content = read_asset_content(version)
    return AssetVersionView(asset=asset, version=version, content=content)


def read_version_by_id(version_id: str) -> AssetVersionView:
    from infra.db import get_connection

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT assets.id as asset_id, assets.workspace_id, assets.kind, assets.ref_id,
                   assets.active_version_id, assets.created_at as asset_created_at,
                   asset_versions.id as version_id, asset_versions.version_index,
                   asset_versions.run_id, asset_versions.model, asset_versions.provider,
                   asset_versions.temperature, asset_versions.max_tokens, asset_versions.retrieval_mode,
                   asset_versions.embed_model, asset_versions.seed, asset_versions.prompt_version,
                   asset_versions.content_path, asset_versions.content_type,
                   asset_versions.citations_json, asset_versions.hits_json,
                   asset_versions.created_at as version_created_at
            FROM asset_versions
            JOIN assets ON assets.id = asset_versions.asset_id
            WHERE asset_versions.id = ?
            """,
            (version_id,),
        ).fetchone()
    if not row:
        raise RuntimeError("Asset version not found.")
    asset = AssetRecord(
        id=row["asset_id"],
        workspace_id=row["workspace_id"],
        kind=row["kind"],
        ref_id=row["ref_id"],
        active_version_id=row["active_version_id"],
        created_at=row["asset_created_at"],
    )
    version = AssetVersionRecord(
        id=row["version_id"],
        asset_id=row["asset_id"],
        version_index=row["version_index"],
        run_id=row["run_id"],
        model=row["model"],
        provider=row["provider"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        retrieval_mode=row["retrieval_mode"],
        embed_model=row["embed_model"],
        seed=row["seed"],
        prompt_version=row["prompt_version"],
        content_path=row["content_path"],
        content_type=row["content_type"],
        citations_json=row["citations_json"],
        hits_json=row["hits_json"],
        created_at=row["version_created_at"],
    )
    content = read_asset_content(version)
    return AssetVersionView(asset=asset, version=version, content=content)


def set_active(asset_id: str, version_id: str) -> None:
    set_active_version(asset_id, version_id)


def diff_versions(asset_id: str, version_a: str, version_b: str) -> str:
    view_a = read_version(asset_id, version_a)
    view_b = read_version(asset_id, version_b)
    return diff_text(view_a.content, view_b.content)


def export_version_citations(
    *,
    workspace_id: str,
    asset_id: str,
    version_id: str,
    formats: list[str],
) -> dict[str, str]:
    view = read_version(asset_id, version_id)
    payload = []
    if view.version.hits_json:
        payload = format_citations_payload(view.version.hits_json)
    return export_citations(
        workspace_id=workspace_id,
        asset_id=asset_id,
        version_id=version_id,
        payload=payload,
        formats=formats,
    )


def course_ref_id(course_id: str) -> str:
    return course_id


def course_explain_ref_id(course_id: str, selection: str, mode: str) -> str:
    return f"{course_id}:{mode}:{_hash_ref(selection)}"


def paper_ref_id(doc_id: str) -> str:
    return doc_id


def paper_aggregate_ref_id(doc_ids: list[str], question: str) -> str:
    key = ",".join(sorted(doc_ids)) + "::" + question.strip()
    return f"aggregate:{_hash_ref(key)}"


def slides_ref_id(doc_id: str, duration: str) -> str:
    return f"{doc_id}:{duration}"


def ask_ref_id(query: str, run_id: str | None) -> str:
    key = f"{run_id or ''}:{query.strip()}"
    return f"ask:{_hash_ref(key)}"
