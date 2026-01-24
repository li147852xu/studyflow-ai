from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PluginContext:
    workspace_id: str
    args: dict[str, Any]


@dataclass
class PluginResult:
    ok: bool
    message: str
    data: dict[str, Any] | None = None


class PluginBase:
    name: str
    version: str
    description: str

    def run(self, context: PluginContext) -> PluginResult:  # pragma: no cover - interface
        raise NotImplementedError()
