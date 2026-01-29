import os
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz

from core.parsing.metadata import PaperMetadata
from infra.db import get_connection
from service.paper_service import ensure_paper


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

        ws_id = _capture([sys.executable, "-m", "cli.main", "workspace", "create", "verify-v2-5"])
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "docs"
            folder.mkdir(parents=True, exist_ok=True)
            _create_pdf(folder / "a.pdf", "Doc A")
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
        if not doc_ids:
            raise RuntimeError("No documents imported.")

        # Create paper records for pack tests
        paper_ids: list[str] = []
        for doc_id in doc_ids:
            paper_id = ensure_paper(
                workspace_id=ws_id,
                doc_id=doc_id,
                metadata=PaperMetadata(title="Title", authors="Author", year="2024"),
            )
            paper_ids.append(paper_id)

        # slides pack
        _run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "pack",
                "make",
                "--workspace",
                ws_id,
                "--type",
                "slides",
                "--source",
                doc_ids[0],
            ]
        )

        # bundle export/import
        bundle_path = _capture(
            [
                sys.executable,
                "-m",
                "cli.main",
                "bundle",
                "export",
                "--workspace",
                ws_id,
                "--with-pdf",
            ]
        )
        new_ws = _capture(
            [
                sys.executable,
                "-m",
                "cli.main",
                "bundle",
                "import",
                "--path",
                bundle_path,
            ]
        )
        with get_connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) as count FROM documents WHERE workspace_id = ?",
                (new_ws,),
            ).fetchone()["count"]
        if count == 0:
            raise RuntimeError("Bundle import did not restore documents.")

        if not _llm_ready():
            print("LLM not configured: slides content may be placeholder.")

    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V2.5 verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
