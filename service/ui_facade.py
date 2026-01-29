from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class UIResult:
    ok: bool
    data: Any | None = None
    error: str | None = None
    hint: str | None = None


def safe_call(
    fn: Callable[..., Any],
    *,
    hint: str | None = None,
    **kwargs: Any,
) -> UIResult:
    try:
        return UIResult(ok=True, data=fn(**kwargs))
    except Exception as exc:  # noqa: BLE001 - UI boundary handler
        return UIResult(ok=False, error=str(exc), hint=hint)
