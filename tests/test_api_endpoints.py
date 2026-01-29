import base64
import os
from pathlib import Path

import fitz
from fastapi.testclient import TestClient


def _create_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "API endpoint test PDF")
    data = doc.tobytes()
    doc.close()
    return data


def test_api_endpoints(tmp_path: Path, monkeypatch):
    os.environ["STUDYFLOW_WORKSPACES_DIR"] = str(tmp_path / "workspaces")
    monkeypatch.setenv("STUDYFLOW_LLM_BASE_URL", "http://example.com")
    monkeypatch.setenv("STUDYFLOW_LLM_MODEL", "test")
    monkeypatch.setenv("STUDYFLOW_LLM_API_KEY", "test")

    import core.agents.paper_agent as paper_agent
    import core.coach.coach_agent as coach_agent
    import service.chat_service as chat_service
    import service.retrieval_service as retrieval_service

    monkeypatch.setattr(chat_service, "chat", lambda *args, **kwargs: "ok")
    monkeypatch.setattr(retrieval_service, "chat", lambda *args, **kwargs: "ok")
    monkeypatch.setattr(paper_agent, "chat", lambda *args, **kwargs: "ok")
    monkeypatch.setattr(coach_agent, "chat", lambda *args, **kwargs: "ok")

    from backend.api import app
    from infra.models import init_db

    init_db()
    client = TestClient(app)

    resp = client.post("/workspaces", json={"action": "create", "name": "api-test"})
    assert resp.status_code == 200
    workspaces = resp.json()["workspaces"]
    assert workspaces
    ws_id = workspaces[0]["id"]

    data = _create_pdf_bytes()
    resp = client.post(
        "/ingest",
        json={
            "workspace_id": ws_id,
            "filename": "doc.pdf",
            "data_base64": base64.b64encode(data).decode("utf-8"),
            "kind": "document",
            "doc_type": "paper",
        },
    )
    assert resp.status_code == 200
    doc_id = resp.json()["doc_id"]

    resp = client.post(
        "/query",
        json={"workspace_id": ws_id, "query": "test", "mode": "bm25", "top_k": 3},
    )
    assert resp.status_code == 200
    assert resp.json()["answer"] == "ok"

    resp = client.post(
        "/generate",
        json={
            "action_type": "paper_card",
            "workspace_id": ws_id,
            "doc_id": doc_id,
            "retrieval_mode": "bm25",
        },
    )
    assert resp.status_code == 200
    asset_id = resp.json().get("asset_id")
    assert asset_id

    resp = client.get(f"/assets/{asset_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()["versions"]
    assert versions

    version_id = versions[0]["id"]
    resp = client.get(f"/assets/{asset_id}/version/{version_id}")
    assert resp.status_code == 200
    assert resp.json()["content"]

    resp = client.get("/ocr/status")
    assert resp.status_code == 200

    resp = client.post(
        "/coach/start",
        json={"workspace_id": ws_id, "problem": "Test problem", "retrieval_mode": "bm25"},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    resp = client.post(
        "/coach/submit",
        json={
            "workspace_id": ws_id,
            "session_id": session_id,
            "answer": "My answer",
            "retrieval_mode": "bm25",
        },
    )
    assert resp.status_code == 200

    resp = client.get("/plugins")
    assert resp.status_code == 200
    assert resp.json()["plugins"]

    resp = client.get("/prompts")
    assert resp.status_code == 200
    assert resp.json()["prompts"]
