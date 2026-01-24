import os
from pathlib import Path

from infra.models import init_db
from service.workspace_service import create_workspace
from core.coach.store import create_session, get_session, list_sessions, update_phase_a, update_phase_b


def test_coach_session_store(tmp_path: Path):
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    init_db()
    ws_id = create_workspace("coach")
    session = create_session(ws_id, "Problem")
    update_phase_a(session.id, "A output", None, None)
    update_phase_b(session.id, "B output", None, None)
    fetched = get_session(session.id)
    assert fetched.phase_a_output == "A output"
    assert fetched.phase_b_output == "B output"
    sessions = list_sessions(ws_id)
    assert sessions
