from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import CitationBundle, build_citation_bundle
from core.prompts.course_prompts import cheatsheet_prompt, explain_prompt, overview_prompt
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits
from core.retrieval.retriever import Hit


class CourseAgentError(RuntimeError):
    pass


@dataclass
class AgentOutput:
    content: str
    citations: list[str]


class CourseAgent:
    def __init__(self, workspace_id: str, course_id: str, doc_ids: list[str]) -> None:
        self.workspace_id = workspace_id
        self.course_id = course_id
        self.doc_ids = doc_ids

    def _retrieve_hits(self, query: str, top_k: int = 8) -> list[Hit]:
        hits = retrieve_hits(
            workspace_id=self.workspace_id,
            query=query,
            top_k=top_k,
            doc_ids=self.doc_ids,
        )
        if not hits:
            raise CourseAgentError("No retrieval hits found for this course.")
        return hits

    def _merge_hits(self, batches: list[list[Hit]]) -> list[Hit]:
        seen = set()
        merged = []
        for batch in batches:
            for hit in batch:
                if hit.chunk_id in seen:
                    continue
                seen.add(hit.chunk_id)
                merged.append(hit)
        return merged

    def generate_overview(self, progress_cb: callable | None = None) -> AgentOutput:
        topics = [
            "课程总览与学习目标",
            "核心概念与基础术语",
            "关键模型与算法",
            "训练/优化与评估",
            "应用场景与案例",
        ]
        # Retrieval rounds: 1 per topic (5 rounds)
        total = len(topics)
        batches = []
        for idx, topic in enumerate(topics, start=1):
            batches.append(self._retrieve_hits(topic, top_k=8))
            if progress_cb:
                progress_cb(idx, total)

        merged_hits = self._merge_hits(batches)
        bundle = build_citation_bundle(merged_hits)
        prompt = overview_prompt(bundle.numbered_context, topics)
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CourseAgentError(str(exc)) from exc
        return AgentOutput(content=content, citations=bundle.citations)

    def generate_cheatsheet(self, progress_cb: callable | None = None) -> AgentOutput:
        sections = [
            "Definitions",
            "Key Formulas",
            "Typical Question Types",
            "Common Pitfalls",
        ]
        total = len(sections)
        batches = []
        for idx, section in enumerate(sections, start=1):
            batches.append(self._retrieve_hits(section, top_k=8))
            if progress_cb:
                progress_cb(idx, total)

        merged_hits = self._merge_hits(batches)
        bundle = build_citation_bundle(merged_hits)
        prompt = cheatsheet_prompt(bundle.numbered_context)
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CourseAgentError(str(exc)) from exc
        return AgentOutput(content=content, citations=bundle.citations)

    def explain_selection(self, selection: str, mode: str) -> AgentOutput:
        bundle = build_citation_bundle(self._retrieve_hits(selection, top_k=8))
        prompt = explain_prompt(selection, mode, bundle.numbered_context)
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CourseAgentError(str(exc)) from exc
        return AgentOutput(content=content, citations=bundle.citations)
