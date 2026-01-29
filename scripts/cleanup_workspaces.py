import shutil

from infra.db import get_workspaces_dir


def main() -> int:
    workspaces_dir = get_workspaces_dir()
    if workspaces_dir.exists():
        shutil.rmtree(workspaces_dir)
    workspaces_dir.mkdir(parents=True, exist_ok=True)
    print(f"Workspace cleaned: {workspaces_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
