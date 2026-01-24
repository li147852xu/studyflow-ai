from __future__ import annotations

from dataclasses import dataclass

from core.llm.providers.openai_compat import OpenAICompatError, chat_completion


class LLMClientError(RuntimeError):
    pass


@dataclass
class LLMSettings:
    base_url: str
    api_key: str
    model: str


class LLMClient:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        seed: int | None = None,
    ) -> str:
        try:
            return chat_completion(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                model=self.settings.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
            )
        except OpenAICompatError as exc:
            raise LLMClientError(str(exc)) from exc
