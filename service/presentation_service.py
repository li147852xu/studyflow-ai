from __future__ import annotations

from pathlib import Path

from core.agents.slides_agent import SlidesAgent, SlidesOutput
from infra.db import get_workspaces_dir
from service.paper_service import list_papers
from service.document_service import list_documents


def list_sources(workspace_id: str) -> list[dict]:
    sources = []
    for doc in list_documents(workspace_id):
        sources.append(
            {
                "label": f"Document: {doc['filename']}",
                "doc_id": doc["id"],
                "type": "document",
            }
        )
    for paper in list_papers(workspace_id):
        sources.append(
            {
                "label": f"Paper: {paper['title']}",
                "doc_id": paper["doc_id"],
                "type": "paper",
            }
        )
    return sources


def generate_slides(
    *,
    workspace_id: str,
    doc_id: str,
    duration: str,
    save_outputs: bool = True,
) -> SlidesOutput:
    output_dir = None
    if save_outputs:
        output_dir = get_workspaces_dir() / workspace_id / "outputs"
    agent = SlidesAgent(workspace_id, doc_id)
    return agent.generate(duration, output_dir=output_dir)
