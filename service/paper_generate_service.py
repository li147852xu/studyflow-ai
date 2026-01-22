from __future__ import annotations

from core.agents.paper_agent import PaperAgent, PaperCardOutput
from core.agents.paper_aggregator import AggregationOutput, PaperAggregator


def generate_paper_card(
    *,
    workspace_id: str,
    doc_id: str,
    progress_cb: callable | None = None,
) -> PaperCardOutput:
    agent = PaperAgent(workspace_id, doc_id)
    return agent.generate_paper_card(progress_cb=progress_cb)


def aggregate_papers(
    *,
    workspace_id: str,
    doc_ids: list[str],
    question: str,
    progress_cb: callable | None = None,
) -> AggregationOutput:
    aggregator = PaperAggregator(workspace_id, doc_ids)
    return aggregator.aggregate(question, progress_cb=progress_cb)
