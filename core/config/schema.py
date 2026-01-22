from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelPreset:
    chat_model: str
    embedding_model: str
    temperature: float = 0.2
    max_tokens: int = 2048


@dataclass
class ProfileConfig:
    name: str
    base_url: str
    api_key_env: str
    chat_model: str
    embedding_model: str
    temperature: float
    max_tokens: int


@dataclass
class AppConfig:
    profile: str
    profiles: dict[str, ProfileConfig]
    workspaces_dir: str
