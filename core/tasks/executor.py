from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor

from core.tasks.runner import run_task

_EXECUTOR: ThreadPoolExecutor | None = None
_FUTURES: dict[str, Future] = {}
_LOCK = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="sf-task")
    return _EXECUTOR


def submit_task(task_id: str) -> bool:
    with _LOCK:
        existing = _FUTURES.get(task_id)
        if existing and not existing.done():
            return False
        future = _get_executor().submit(run_task, task_id)
        _FUTURES[task_id] = future
    return True


def shutdown_executor(wait: bool = True, cancel_futures: bool = False) -> None:
    global _EXECUTOR
    with _LOCK:
        executor = _EXECUTOR
        _EXECUTOR = None
        _FUTURES.clear()
    if executor:
        try:
            executor.shutdown(wait=wait, cancel_futures=cancel_futures)
        except Exception:
            pass
