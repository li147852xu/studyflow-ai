from __future__ import annotations

import fnmatch
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FolderFile:
    path: Path
    sha256: str


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_folder(
    root: Path,
    *,
    ignore_globs: list[str] | None = None,
) -> list[FolderFile]:
    ignore_globs = ignore_globs or []
    supported_exts = [
        ".pdf",
        ".txt",
        ".md",
        ".docx",
        ".pptx",
        ".html",
        ".htm",
        ".png",
        ".jpg",
        ".jpeg",
    ]
    files: list[FolderFile] = []
    for ext in supported_exts:
        for path in root.rglob(f"*{ext}"):
            rel = str(path.relative_to(root))
            if any(fnmatch.fnmatch(rel, pattern) for pattern in ignore_globs):
                continue
            files.append(FolderFile(path=path, sha256=_sha256_path(path)))
    return files
