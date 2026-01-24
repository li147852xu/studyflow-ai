from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PackManifest:
    pack_type: str
    workspace_id: str
    created_at: str
    source_id: str
    items: list[str]


def build_manifest(
    *, pack_type: str, workspace_id: str, source_id: str, items: list[str]
) -> PackManifest:
    return PackManifest(
        pack_type=pack_type,
        workspace_id=workspace_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        source_id=source_id,
        items=items,
    )


def dump_manifest(manifest: PackManifest) -> str:
    return json.dumps(manifest.__dict__, ensure_ascii=False, indent=2)
