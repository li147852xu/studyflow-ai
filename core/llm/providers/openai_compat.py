from __future__ import annotations

import requests


class OpenAICompatError(RuntimeError):
    pass


def chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
    seed: int | None = None,
    timeout: int = 180,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None and max_tokens > 0:
        payload["max_tokens"] = max_tokens
    if seed is not None and seed > 0:
        payload["seed"] = seed
    last_exc: Exception | None = None
    for _ in range(3):
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=timeout
            )
            response.raise_for_status()
            last_exc = None
            break
        except requests.Timeout as exc:
            last_exc = exc
            continue
        except requests.RequestException as exc:
            raise OpenAICompatError(f"LLM request failed: {exc}") from exc
    if last_exc is not None:
        raise OpenAICompatError(f"LLM request failed: {last_exc}") from last_exc

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenAICompatError("Unexpected LLM response format.") from exc
