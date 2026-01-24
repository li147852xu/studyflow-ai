import os
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.api import app
from infra.models import init_db
from service.asset_service import create_asset_version, list_versions
from core.retrieval.retriever import Hit


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def _create_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Verify v1.3 PDF")
    doc.save(path)
    doc.close()


def main() -> int:
    try:
        init_db()
        _run([sys.executable, "-m", "compileall", "."])
        _run([sys.executable, "-m", "pytest", "-q"])

        client = TestClient(app)
        resp = client.get("/health")
        if resp.status_code != 200:
            raise RuntimeError("FastAPI health check failed.")

        ws_id = _capture([sys.executable, "-m", "cli.main", "workspace", "create", "verify-v1-3"])

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "verify.pdf"
            _create_pdf(pdf_path)
            ingest_out = _capture(
                [sys.executable, "-m", "cli.main", "ingest", "--workspace", ws_id, str(pdf_path)]
            )
        doc_id = ingest_out.split()[0]

        _run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "query",
                "--workspace",
                ws_id,
                "--mode",
                "bm25",
                "test",
            ]
        )

        llm_ready = bool(os.getenv("STUDYFLOW_LLM_API_KEY"))
        if llm_ready:
            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "gen",
                    "--workspace",
                    ws_id,
                    "--type",
                    "slides",
                    "--source",
                    doc_id,
                    "--duration",
                    "10",
                    "--mode",
                    "bm25",
                ]
            )

        asset_list = _capture([sys.executable, "-m", "cli.main", "asset", "ls", "--workspace", ws_id])
        if not asset_list or asset_list.startswith("No assets"):
            hits = [
                Hit(
                    chunk_id="c1",
                    doc_id=doc_id,
                    workspace_id=ws_id,
                    filename="verify.pdf",
                    page_start=1,
                    page_end=1,
                    text="test",
                    score=1.0,
                )
            ]
            version = create_asset_version(
                workspace_id=ws_id,
                kind="slides",
                ref_id=f"{doc_id}:10",
                content="deck",
                content_type="markdown",
                run_id="run",
                model="test",
                provider=None,
                temperature=None,
                max_tokens=None,
                retrieval_mode=None,
                embed_model=None,
                seed=None,
                prompt_version="v1",
                hits=hits,
            )
            asset_id = version.asset_id
            versions = list_versions(asset_id)
        else:
            asset_id = asset_list.split()[0]
            versions = list_versions(asset_id)

        if len(versions) < 2:
            create_asset_version(
                workspace_id=ws_id,
                kind="slides",
                ref_id=f"{doc_id}:10",
                content="deck v2",
                content_type="markdown",
                run_id="run-2",
                model="test",
                provider=None,
                temperature=None,
                max_tokens=None,
                retrieval_mode=None,
                embed_model=None,
                seed=None,
                prompt_version="v1",
                hits=[],
            )
            versions = list_versions(asset_id)

        v1 = versions[0].id
        v2 = versions[-1].id

        _run([sys.executable, "-m", "cli.main", "asset", "show", "--asset", asset_id, "--version", v1])
        _run([sys.executable, "-m", "cli.main", "asset", "pin", "--asset", asset_id, "--version", v1])
        _run([sys.executable, "-m", "cli.main", "asset", "rollback", "--asset", asset_id, "--version", v2])
        _run([sys.executable, "-m", "cli.main", "asset", "diff", "--asset", asset_id, "--a", v1, "--b", v2])
        _run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "asset",
                "export-citations",
                "--asset",
                asset_id,
                "--version",
                v1,
                "--format",
                "both",
            ]
        )

        _run([sys.executable, "-m", "cli.main", "doctor"])
        __import__("app.main")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V1.3 verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
