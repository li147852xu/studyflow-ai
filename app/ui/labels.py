from __future__ import annotations

from app.ui.i18n import current_language


def L(zh: str, en: str) -> str:
    return zh if current_language().startswith("zh") else en
