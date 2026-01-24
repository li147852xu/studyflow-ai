import os
import sys
import tempfile
import subprocess
from pathlib import Path

import fitz

from infra.db import get_connection, get_workspaces_dir
from service.tasks_service import enqueue_ingest_task


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def _create_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def _llm_ready() -> bool:
    return bool(os.getenv("STUDYFLOW_LLM_BASE_URL")) and bool(os.getenv("STUDYFLOW_LLM_MODEL")) and bool(
        os.getenv("STUDYFLOW_LLM_API_KEY")
    )


def main() -> int:
    try:
        _run([sys.executable, "-m", "compileall", "."])
        _run([sys.executable, "-m", "pytest", "-q"])

        ws_id = _capture([sys.executable, "-m", "cli.main", "workspace", "create", "verify-v2-8"])

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "doc.pdf"
            _create_pdf(pdf_path, "Doc for v2.8")

            # Task-based ingest via CLI
            ingest_output = _capture(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "ingest",
                    "--workspace",
                    ws_id,
                    str(pdf_path),
                ]
            )
            parts = ingest_output.split()
            task_id = parts[0]
            doc_id = parts[1]
            _run([sys.executable, "-m", "cli.main", "tasks", "show", task_id])
            _run([sys.executable, "-m", "cli.main", "tasks", "ls", "--workspace", ws_id])

            # Cancel + retry a task
            task_retry = enqueue_ingest_task(
                workspace_id=ws_id,
                path=str(pdf_path),
                ocr_mode="off",
                ocr_threshold=50,
                save_dir=str(get_workspaces_dir() / ws_id / "docs"),
            )
            _run([sys.executable, "-m", "cli.main", "tasks", "cancel", task_retry])
            _run([sys.executable, "-m", "cli.main", "tasks", "retry", task_retry])
            _run([sys.executable, "-m", "cli.main", "tasks", "resume", task_retry])

        # Query (LLM optional)
        _run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "query",
                "--workspace",
                ws_id,
                "test query",
            ]
        )

        # Generation (LLM optional)
        if _llm_ready():
            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "gen",
                    "--workspace",
                    ws_id,
                    "--type",
                    "paper_card",
                    "--source",
                    doc_id,
                ]
            )
        else:
            print(
                "LLM not configured: skipping gen step. "
                "Set STUDYFLOW_LLM_BASE_URL/STUDYFLOW_LLM_MODEL/STUDYFLOW_LLM_API_KEY."
            )

        # Index maintenance commands
        _run([sys.executable, "-m", "cli.main", "doctor"])
        _run([sys.executable, "-m", "cli.main", "index", "status", ws_id])
        _run([sys.executable, "-m", "cli.main", "index", "rebuild", ws_id])
        _run([sys.executable, "-m", "cli.main", "index", "vacuum", ws_id])

        # Doctor deep
        _run([sys.executable, "-m", "cli.main", "doctor", "--deep", "--workspace", ws_id])

        # Clean dry-run + apply
        _run([sys.executable, "-m", "cli.main", "clean", "--workspace", ws_id])
        _run([sys.executable, "-m", "cli.main", "clean", "--workspace", ws_id, "--apply", "--yes"])

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V2.8 verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
