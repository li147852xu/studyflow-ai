from __future__ import annotations

import json

from core.ingest.cite import build_citation
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
        citation = build_citation(
            filename=hit.get("filename") or "-",
            page_start=int(hit.get("page_start") or 0),
            page_end=int(hit.get("page_end") or 0),
            text=hit.get("text") or "",
            file_type=hit.get("file_type"),
        )
        payload.append(
            {
                "chunk_id": hit.get("chunk_id"),
                "filename": hit.get("filename"),
                "file_type": hit.get("file_type"),
                "page_start": hit.get("page_start"),
                "page_end": hit.get("page_end"),
                "location": citation.location_label,
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
            location = item.get("location") or f"p.{item.get('page_start')}-{item.get('page_end')}"
            line = f"{item.get('filename')} {location} [{item.get('chunk_id')}] {item.get('snippet')}"
            lines.append(line)
        path.write_text("\n".join(lines), encoding="utf-8")
        paths["txt"] = str(path)
    return paths
