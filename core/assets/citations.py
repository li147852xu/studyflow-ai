from __future__ import annotations

import json
from pathlib import Path

from infra.db import get_workspaces_dir


def format_citations_payload(hits_json: str | None) -> list[dict]:
    if not hits_json:
        return []
    try:
        hits = json.loads(hits_json)
    except json.JSONDecodeError:
        return []
    payload = []
    for hit in hits:
        text = (hit.get("text") or "").strip().replace("\n", " ")
        snippet = text[:240] + ("..." if len(text) > 240 else "")
        payload.append(
            {
                "chunk_id": hit.get("chunk_id"),
                "filename": hit.get("filename"),
                "page_start": hit.get("page_start"),
                "page_end": hit.get("page_end"),
                "snippet": snippet,
            }
        )
    return payload


def export_citations(
    *,
    workspace_id: str,
    asset_id: str,
    version_id: str,
    payload: list[dict],
    formats: list[str],
) -> dict[str, str]:
    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "citations"
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    if "json" in formats:
        path = output_dir / f"{asset_id}_{version_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        paths["json"] = str(path)
    if "txt" in formats:
        path = output_dir / f"{asset_id}_{version_id}.txt"
        lines = []
        for item in payload:
            line = (
                f"{item.get('filename')} p.{item.get('page_start')}-{item.get('page_end')} "
                f"[{item.get('chunk_id')}] {item.get('snippet')}"
            )
            lines.append(line)
        path.write_text("\n".join(lines), encoding="utf-8")
        paths["txt"] = str(path)
    return paths
