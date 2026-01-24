from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class BundleManifest:
    version: str
    workspace_id: str
    created_at: str
    options: dict
    counts: dict


def build_manifest(
    *, version: str, workspace_id: str, options: dict, counts: dict
) -> BundleManifest:
    return BundleManifest(
        version=version,
        workspace_id=workspace_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        options=options,
        counts=counts,
    )


def dump_manifest(manifest: BundleManifest) -> str:
    return json.dumps(manifest.__dict__, ensure_ascii=False, indent=2)
