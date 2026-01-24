import os
import sys
import tempfile
import subprocess
from pathlib import Path

import fitz

from infra.db import get_connection
from service.paper_service import ensure_paper
from core.parsing.metadata import PaperMetadata


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

        ws_id = _capture([sys.executable, "-m", "cli.main", "workspace", "create", "verify-v2-4"])
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "papers"
            folder.mkdir(parents=True, exist_ok=True)
            _create_pdf(folder / "p1.pdf", "Paper One")
            _create_pdf(folder / "p2.pdf", "Paper Two")
            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "import",
                    "folder",
                    "--workspace",
                    ws_id,
                    "--path",
                    str(folder),
                ]
            )

        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id FROM documents WHERE workspace_id = ?",
                (ws_id,),
            ).fetchall()
        doc_ids = [row["id"] for row in rows]
        paper_ids: list[str] = []
        for doc_id in doc_ids:
            paper_id = ensure_paper(
                workspace_id=ws_id,
                doc_id=doc_id,
                metadata=PaperMetadata(title="Title", authors="Author", year="2024"),
            )
            paper_ids.append(paper_id)

        if _llm_ready():
            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "concepts",
                    "build",
                    "--workspace",
                    ws_id,
                    "--papers",
                    *paper_ids,
                ]
            )
            _run(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "concepts",
                    "search",
                    "--workspace",
                    ws_id,
                    "paper",
                ]
            )
            create_out = _capture(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "related",
                    "create",
                    "--workspace",
                    ws_id,
                    "--papers",
                    *paper_ids,
                    "--topic",
                    "Transformer related work",
                ]
            )
            project_line = [line for line in create_out.splitlines() if "project_id:" in line]
            if project_line:
                project_id = project_line[-1].split("project_id:")[-1].strip()
                _run(
                    [
                        sys.executable,
                        "-m",
                        "cli.main",
                        "related",
                        "update",
                        "--workspace",
                        ws_id,
                        "--project",
                        project_id,
                        "--add-papers",
                        paper_ids[0],
                    ]
                )
                _run(
                    [
                        sys.executable,
                        "-m",
                        "cli.main",
                        "related",
                        "export",
                        "--workspace",
                        ws_id,
                        "--project",
                        project_id,
                        "--format",
                        "txt",
                    ]
                )
        else:
            print("LLM not configured: skipping concepts/related generation.")

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V2.4 verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
