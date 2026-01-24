from __future__ import annotations

import re
from pathlib import Path

import requests


class DownloadError(RuntimeError):
    pass


def _ensure_pdf(response: requests.Response) -> None:
    content_type = response.headers.get("Content-Type", "")
    if "pdf" not in content_type.lower():
        raise DownloadError("URL did not return a PDF.")


def download_arxiv(arxiv_id: str) -> tuple[bytes, str]:
    safe_id = arxiv_id.strip()
    url = f"https://arxiv.org/pdf/{safe_id}.pdf"
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise DownloadError(f"arXiv download failed ({response.status_code}).")
    _ensure_pdf(response)
    filename = f"arxiv_{safe_id}.pdf"
    return response.content, filename


def download_url(url: str) -> tuple[bytes, str]:
    response = requests.get(url, timeout=30, allow_redirects=True)
    if response.status_code != 200:
        raise DownloadError(f"Download failed ({response.status_code}).")
    _ensure_pdf(response)
    name = Path(url.split("?")[0]).name or "download.pdf"
    if not name.endswith(".pdf"):
        name = f"{name}.pdf"
    return response.content, name


def download_doi(doi: str) -> tuple[bytes, str]:
    clean = doi.strip()
    url = f"https://doi.org/{clean}"
    headers = {"Accept": "application/pdf"}
    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    if response.status_code != 200:
        raise DownloadError(f"DOI resolution failed ({response.status_code}).")
    _ensure_pdf(response)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", clean).strip("_")
    filename = f"doi_{slug}.pdf"
    return response.content, filename
