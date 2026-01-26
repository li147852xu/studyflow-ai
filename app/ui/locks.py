from __future__ import annotations

from service.tasks_service import list_tasks_for_workspace


def running_task_summary(workspace_id: str | None) -> tuple[bool, str]:
    if not workspace_id:
        return False, ""
    try:
        tasks = list_tasks_for_workspace(workspace_id=workspace_id)
    except Exception:
        return False, ""
    for task in tasks:
        status = task["status"] if isinstance(task, dict) else task.status
        if status in {"queued", "running"}:
            task_type = task["type"] if isinstance(task, dict) else task.type
            return True, f"Task running: {task_type} — please wait until it completes."
    return False, ""
