import json
import time
from pathlib import Path

import fitz

from infra.db import get_workspaces_dir
from service.workspace_service import create_workspace
from service.tasks_service import enqueue_ingest_task, run_task_by_id, enqueue_index_task
from service.retrieval_service import retrieve_hits_mode, RetrievalError


def _create_pdf(path: Path, pages: int) -> None:
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Benchmark query page {index + 1}")
    doc.save(path)
    doc.close()


def main() -> None:
    workspace_id = create_workspace("bench-query")
    tmp_dir = Path(get_workspaces_dir()) / workspace_id / "bench"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = tmp_dir / "bench.pdf"
    _create_pdf(pdf_path, pages=2)

    ingest_task = enqueue_ingest_task(
        workspace_id=workspace_id,
        path=str(pdf_path),
        ocr_mode="off",
        ocr_threshold=50,
    )
    run_task_by_id(ingest_task)

    index_task = enqueue_index_task(workspace_id=workspace_id, reset=True)
    try:
        run_task_by_id(index_task)
    except Exception:
        pass

    results = {}
    for mode in ["vector", "bm25", "hybrid"]:
        start = time.perf_counter()
        try:
            hits, used = retrieve_hits_mode(
                workspace_id=workspace_id, query="benchmark query", mode=mode, top_k=5
            )
            elapsed = int((time.perf_counter() - start) * 1000)
            results[mode] = {
                "mode": used,
                "hit_count": len(hits),
                "latency_ms": elapsed,
            }
        except RetrievalError as exc:
            results[mode] = {"mode": mode, "error": str(exc)}

    output_dir = get_workspaces_dir() / workspace_id / "outputs" / "benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"bench_query_{int(time.time())}.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
