from __future__ import annotations

SECRET_KEYS = {"api_key", "token", "authorization", "secret", "password"}


def sanitize_dict(payload: dict) -> dict:
    cleaned = {}
    for key, value in payload.items():
        if any(secret in key.lower() for secret in SECRET_KEYS):
            continue
        if isinstance(value, dict):
            cleaned[key] = sanitize_dict(value)
        else:
            cleaned[key] = value
    return cleaned
