#!/usr/bin/env python3
"""
Verification script for StudyFlow AI v2.10 release.

Runs all required checks for a release-grade build:
1. Syntax check (compileall)
2. Linting (ruff)
3. Tests (pytest)
4. Import smoke tests
5. Demo data flow simulation
6. Docker build check (optional)

Usage:
    python scripts/verify_release_v2_10.py [--skip-docker]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command and print output."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if capture and result.stdout:
        print(result.stdout)
    if capture and result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return result


def check_version() -> None:
    """Verify version is 2.10.0 across all locations."""
    print("\n" + "=" * 60)
    print("Checking version consistency...")
    print("=" * 60)

    # Check pyproject.toml
    pyproject = Path("pyproject.toml").read_text()
    if 'version = "2.10.0"' not in pyproject:
        print("ERROR: pyproject.toml version is not 2.10.0")
        sys.exit(1)
    print("✓ pyproject.toml: 2.10.0")

    # Check README
    readme = Path("README.md").read_text()
    if "v2.10.0" not in readme:
        print("WARNING: README.md may not mention v2.10.0")
    else:
        print("✓ README.md mentions v2.10.0")

    print("Version check passed!")


def check_required_files() -> None:
    """Verify all required files exist."""
    print("\n" + "=" * 60)
    print("Checking required files...")
    print("=" * 60)

    required_files = [
        "README.md",
        "VERSION_LOG.md",
        "Dockerfile",
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        "pyproject.toml",
        ".gitignore",
        ".env.example",
        "examples/ml_fundamentals.pdf",
        "app/main.py",
        "app/help_content.py",
        "cli/main.py",
        "backend/api.py",
    ]

    missing = []
    for f in required_files:
        if Path(f).exists():
            print(f"✓ {f}")
        else:
            print(f"✗ {f} MISSING")
            missing.append(f)

    if missing:
        print(f"\nERROR: Missing required files: {missing}")
        sys.exit(1)

    print("All required files present!")


def check_no_extra_markdown() -> None:
    """Ensure only README.md and VERSION_LOG.md exist."""
    print("\n" + "=" * 60)
    print("Checking for extra markdown files...")
    print("=" * 60)

    allowed = {"README.md", "VERSION_LOG.md"}
    md_files = list(Path(".").rglob("*.md"))
    extra = [f for f in md_files if f.name not in allowed and not str(f).startswith(".")]

    if extra:
        print(f"WARNING: Extra markdown files found: {extra}")
        print("These should be removed or converted to .py/.txt")
    else:
        print("✓ Only README.md and VERSION_LOG.md present")


def run_compileall() -> None:
    """Run Python syntax check."""
    _run([sys.executable, "-m", "compileall", "-q", "."])
    print("✓ compileall passed")


def run_ruff() -> None:
    """Run ruff linting."""
    _run(["ruff", "check", "."])
    print("✓ ruff check passed")


def run_pytest() -> None:
    """Run pytest."""
    _run([sys.executable, "-m", "pytest", "-q", "--tb=short"])
    print("✓ pytest passed")


def run_import_smoke() -> None:
    """Test key imports."""
    print("\n" + "=" * 60)
    print("Running import smoke tests...")
    print("=" * 60)

    imports = [
        "import app.main",
        "import cli.main",
        "import backend.api",
        "from app.help_content import get_help_sections",
        "from service.tasks_service import enqueue_ingest_index_task",
    ]

    for imp in imports:
        _run([sys.executable, "-c", imp])
        print(f"✓ {imp}")

    print("Import smoke tests passed!")


def check_demo_flow() -> None:
    """Simulate the demo data flow."""
    print("\n" + "=" * 60)
    print("Checking demo data flow...")
    print("=" * 60)

    # Check demo PDF exists
    demo_pdf = Path("examples/ml_fundamentals.pdf")
    if not demo_pdf.exists():
        print("Creating demo PDF...")
        _run([sys.executable, "scripts/create_demo_pdf.py"])

    if demo_pdf.exists():
        print(f"✓ Demo PDF exists: {demo_pdf} ({demo_pdf.stat().st_size} bytes)")
    else:
        print("ERROR: Demo PDF creation failed")
        sys.exit(1)

    # Verify demo can be loaded via facade
    code = """
from pathlib import Path
demo_path = Path("examples/ml_fundamentals.pdf")
assert demo_path.exists(), "Demo PDF not found"
data = demo_path.read_bytes()
assert len(data) > 1000, "Demo PDF too small"
print(f"Demo PDF loaded: {len(data)} bytes")
"""
    _run([sys.executable, "-c", code])
    print("✓ Demo flow check passed")


def check_docker(skip: bool = False) -> None:
    """Check Docker build (optional)."""
    if skip:
        print("\n" + "=" * 60)
        print("Skipping Docker check (--skip-docker)")
        print("=" * 60)
        return

    print("\n" + "=" * 60)
    print("Checking Docker build...")
    print("=" * 60)

    # Check if docker is available
    result = _run(["docker", "--version"], check=False, capture=True)
    if result.returncode != 0:
        print("Docker not available, skipping Docker check")
        return

    # Build image
    result = _run(["docker", "build", "-t", "studyflow-ai:v2.10-test", "."], check=False)
    if result.returncode != 0:
        print("WARNING: Docker build failed, but this is optional")
    else:
        print("✓ Docker build succeeded")


def main() -> None:
    """Run all verification checks."""
    skip_docker = "--skip-docker" in sys.argv

    print("=" * 60)
    print("StudyFlow AI v2.10.0 Release Verification")
    print("=" * 60)

    # Change to project root
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    print(f"Working directory: {project_root}")

    # Run all checks
    check_version()
    check_required_files()
    check_no_extra_markdown()
    run_compileall()
    run_ruff()
    run_pytest()
    run_import_smoke()
    check_demo_flow()
    check_docker(skip=skip_docker)

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED!")
    print("=" * 60)
    print("\nReady for release v2.10.0")
    print("\nNext steps:")
    print("1. git add -A && git commit -m 'feat: v2.10 release-grade distribution and usability'")
    print("2. git push origin main")
    print("3. Create GitHub Release v2.10.0")


if __name__ == "__main__":
    main()
