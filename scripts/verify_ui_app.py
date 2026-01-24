from __future__ import annotations

import uuid

from core.ui_state.storage import add_history, clear_history, get_setting, set_setting, list_history
from service.workspace_service import create_workspace, delete_workspace
from service.retrieval_service import index_status


def _smoke_imports() -> None:
    import app.main  # noqa: F401
    import app.components.nav  # noqa: F401
    import app.components.shell  # noqa: F401
    import app.components.library_panel  # noqa: F401
    import app.components.workflow_wizard  # noqa: F401
    import app.components.tasks_center  # noqa: F401
    import app.components.exports_center  # noqa: F401
    import app.components.plugins_center  # noqa: F401
    import app.components.settings_center  # noqa: F401
    import app.components.diagnostics_center  # noqa: F401
    import app.components.help_center  # noqa: F401
    import app.components.result_viewer  # noqa: F401


def main() -> None:
    _smoke_imports()
    workspace_name = f"ui_verify_{uuid.uuid4().hex[:8]}"
    workspace_id = create_workspace(workspace_name)
    try:
        set_setting(None, "ui_verify", "1")
        assert get_setting(None, "ui_verify") == "1"

        add_history(
            workspace_id=workspace_id,
            action_type="ui_verify",
            summary="UI verification entry",
            preview="ui verify preview",
            source_ref=None,
            citations_count=0,
            run_id=None,
        )
        history = list_history(workspace_id)
        assert history, "History entry not created"
        clear_history(workspace_id)

        status = index_status(workspace_id)
        assert isinstance(status, dict)
    finally:
        delete_workspace(workspace_id)

    print("verify_ui_app: ok")


if __name__ == "__main__":
    main()
