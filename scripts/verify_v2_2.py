import os
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.api import app
from core.ingest.ocr import OCRSettings, ocr_available


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8").strip()


def _create_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Verify v2.2 PDF")
    doc.save(path)
    doc.close()


def main() -> int:
    try:
        _run([sys.executable, "-m", "compileall", "."])
        _run([sys.executable, "-m", "pytest", "-q"])

        client = TestClient(app)
        resp = client.get("/health")
        if resp.status_code != 200:
            raise RuntimeError("FastAPI health check failed.")
        resp = client.get("/ocr/status")
        if resp.status_code != 200:
            raise RuntimeError("OCR status check failed.")

        ws_id = _capture([sys.executable, "-m", "cli.main", "workspace", "create", "verify-v2-2"])
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "verify.pdf"
            _create_pdf(pdf_path)
            ingest_out = _capture(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "ingest",
                    "--workspace",
                    ws_id,
                    "--ocr",
                    "auto",
                    str(pdf_path),
                ]
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

        llm_ready = bool(os.getenv("STUDYFLOW_LLM_API_KEY"))
        if llm_ready:
            output = _capture(
                [
                    sys.executable,
                    "-m",
                    "cli.main",
                    "coach",
                    "start",
                    "--workspace",
                    ws_id,
                    "--problem",
                    "Explain the topic.",
                ]
            )
            session_line = [line for line in output.splitlines() if "session_id:" in line]
            if session_line:
                session_id = session_line[-1].split("session_id:")[-1].strip()
                _run(
                    [
                        sys.executable,
                        "-m",
                        "cli.main",
                        "coach",
                        "submit",
                        "--workspace",
                        ws_id,
                        "--session",
                        session_id,
                        "--answer",
                        "My attempt.",
                    ]
                )
        else:
            print("Coach CLI skipped: LLM not configured.")

        _run([sys.executable, "-m", "cli.main", "plugins", "ls"])
        _run(
            [
                sys.executable,
                "-m",
                "cli.main",
                "plugins",
                "run",
                "importer_folder",
                "--workspace",
                ws_id,
                "--path",
                "examples",
            ]
        )

        _run([sys.executable, "-m", "cli.main", "doctor"])

        ok, reason = ocr_available(OCRSettings())
        if not ok:
            print(f"OCR unavailable: {reason}")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print("V2.2 verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
