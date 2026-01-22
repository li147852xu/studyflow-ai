import os
from pathlib import Path

from core.config.loader import load_config, apply_profile


def test_config_loader(tmp_path: Path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
default_profile = "openai"

[profiles.openai]
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
chat_model = "gpt-4o-mini"
embedding_model = "text-embedding-3-small"
temperature = 0.2
max_tokens = 2048
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("STUDYFLOW_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    config = load_config()
    apply_profile(config)
    assert os.getenv("STUDYFLOW_LLM_BASE_URL") == "https://api.openai.com/v1"
    assert os.getenv("STUDYFLOW_LLM_MODEL") == "gpt-4o-mini"
