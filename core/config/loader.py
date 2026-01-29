from __future__ import annotations

import os
import sys
from pathlib import Path

# tomllib is only available in Python 3.11+
# Use tomli as fallback for Python 3.10
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError(
            "tomli is required for Python < 3.11. Install with: pip install tomli"
        )

from core.config.schema import AppConfig, ProfileConfig


class ConfigError(RuntimeError):
    pass


def load_config(config_path: str | None = None) -> AppConfig:
    env_profile = os.getenv("STUDYFLOW_PROFILE", "").strip() or None
    workspaces_dir = os.getenv("STUDYFLOW_WORKSPACES_DIR", "./workspaces").strip()
    if config_path:
        path = Path(config_path)
    else:
        path = Path(os.getenv("STUDYFLOW_CONFIG_PATH", "config.toml"))

    if not path.exists():
        raise ConfigError(
            "Missing config file. Create config.toml or set STUDYFLOW_CONFIG_PATH."
        )

    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    profiles_raw = raw.get("profiles", {})
    if not profiles_raw:
        raise ConfigError("No profiles found in config.")

    profiles: dict[str, ProfileConfig] = {}
    for name, data in profiles_raw.items():
        profiles[name] = ProfileConfig(
            name=name,
            base_url=data.get("base_url", ""),
            api_key_env=data.get("api_key_env", ""),
            chat_model=data.get("chat_model", ""),
            embedding_model=data.get("embedding_model", ""),
            temperature=float(data.get("temperature", 0.2)),
            max_tokens=int(data.get("max_tokens", 2048)),
        )

    profile_name = env_profile or raw.get("default_profile") or next(iter(profiles))
    if profile_name not in profiles:
        raise ConfigError("Selected profile not found in config.")

    return AppConfig(
        profile=profile_name,
        profiles=profiles,
        workspaces_dir=workspaces_dir,
    )


def apply_profile(config: AppConfig) -> None:
    profile = config.profiles[config.profile]
    if profile.base_url and not os.getenv("STUDYFLOW_LLM_BASE_URL"):
        os.environ["STUDYFLOW_LLM_BASE_URL"] = profile.base_url
    if profile.chat_model and not os.getenv("STUDYFLOW_LLM_MODEL"):
        os.environ["STUDYFLOW_LLM_MODEL"] = profile.chat_model
    if profile.embedding_model and not os.getenv("STUDYFLOW_EMBED_MODEL"):
        os.environ["STUDYFLOW_EMBED_MODEL"] = profile.embedding_model
    if profile.api_key_env:
        api_key = os.getenv(profile.api_key_env, "")
        if api_key:
            if not os.getenv("STUDYFLOW_LLM_API_KEY"):
                os.environ["STUDYFLOW_LLM_API_KEY"] = api_key
    if not os.getenv("STUDYFLOW_WORKSPACES_DIR"):
        os.environ["STUDYFLOW_WORKSPACES_DIR"] = config.workspaces_dir
