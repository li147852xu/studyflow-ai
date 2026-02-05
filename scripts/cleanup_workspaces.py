import argparse
import shutil

from infra.db import get_workspaces_dir
from service.workspace_service import delete_workspace_except, list_workspaces


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean up workspaces")
    parser.add_argument(
        "--keep",
        nargs="*",
        default=["test1"],
        help="Workspace names to keep (default: test1)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Delete ALL workspaces including test1",
    )
    args = parser.parse_args()
    
    workspaces_dir = get_workspaces_dir()
    
    if args.all:
        # Delete everything
        if workspaces_dir.exists():
            shutil.rmtree(workspaces_dir)
        workspaces_dir.mkdir(parents=True, exist_ok=True)
        print(f"All workspaces cleaned: {workspaces_dir}")
        return 0
    
    # List before
    workspaces_before = list_workspaces()
    print(f"Workspaces before: {len(workspaces_before)}")
    for ws in workspaces_before:
        print(f"  - {ws['name']} ({ws['id']})")
    
    # Delete all except keep list
    keep_names = args.keep
    deleted_count = delete_workspace_except(keep_names)
    
    # Clean up orphaned workspace directories
    workspaces_after = list_workspaces()
    valid_ids = {ws["id"] for ws in workspaces_after}
    
    if workspaces_dir.exists():
        for child in workspaces_dir.iterdir():
            if child.is_dir() and child.name not in valid_ids:
                print(f"Removing orphan directory: {child.name}")
                shutil.rmtree(child)
    
    print(f"\nDeleted {deleted_count} workspaces")
    print(f"Kept: {keep_names}")
    
    # List after
    print(f"\nWorkspaces after: {len(workspaces_after)}")
    for ws in workspaces_after:
        print(f"  - {ws['name']} ({ws['id']})")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
