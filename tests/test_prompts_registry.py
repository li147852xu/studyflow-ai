import json
import os
from pathlib import Path

from core.prompts.registry import build_prompt
from infra.models import init_db
from service.workspace_service import create_workspace


def test_prompts_registry_override(tmp_path: Path):
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("prompts")
    override_path = Path(os.environ["STUDYFLOW_WORKSPACES_DIR"]) / ws_id / "prompts_override.json"
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_payload = {
        "prompts": {
            "course_overview": {"v1": "OVERRIDE {context} {topics}"}
        }
    }
    override_path.write_text(json.dumps(override_payload), encoding="utf-8")
    prompt, version = build_prompt(
        "course_overview",
        ws_id,
        context="ctx",
        topics=["a"],
    )
    assert version == "v1"
    assert prompt.startswith("OVERRIDE")
