import json
import time
from pathlib import Path

import fitz

from infra.db import get_workspaces_dir
from service.tasks_service import enqueue_ingest_task, run_task_by_id
from service.workspace_service import create_workspace


def _create_pdf(path: Path, pages: int) -> None:
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Benchmark page {index + 1}")
    doc.save(path)
    doc.close()


def main() -> None:
    workspace_id = create_workspace("bench-ingest")
    tmp_dir = Path(get_workspaces_dir()) / workspace_id / "bench"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = tmp_dir / "bench.pdf"
    _create_pdf(pdf_path, pages=3)

    start = time.perf_counter()
    task_id = enqueue_ingest_task(
        workspace_id=workspace_id,
        path=str(pdf_path),
        ocr_mode="off",
        ocr_threshold=50,
    )
    result = run_task_by_id(task_id)
    latency_ms = int((time.perf_counter() - start) * 1000)

    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": task_id,
        "doc_id": result["doc_id"],
        "page_count": result["page_count"],
        "chunk_count": result["chunk_count"],
        "latency_ms": latency_ms,
    }
    output_path = output_dir / f"bench_ingest_{int(time.time())}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
