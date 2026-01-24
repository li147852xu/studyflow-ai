from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import CitationBundle, build_citation_bundle
from core.prompts.registry import build_prompt
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode
from core.retrieval.retriever import Hit


class CourseAgentError(RuntimeError):
    pass


@dataclass
class AgentOutput:
    content: str
    citations: list[str]
    hits: list[Hit]
    retrieval_mode: str
    run_id: str | None = None
    asset_id: str | None = None
    asset_version_id: str | None = None
    asset_version_index: int | None = None
    prompt_version: str | None = None


class CourseAgent:
    def __init__(
        self,
        workspace_id: str,
        course_id: str,
        doc_ids: list[str],
        retrieval_mode: str,
    ) -> None:
        self.workspace_id = workspace_id
        self.course_id = course_id
        self.doc_ids = doc_ids
        self.retrieval_mode = retrieval_mode

    def _retrieve_hits(self, query: str, top_k: int = 8) -> tuple[list[Hit], str]:
        hits, used_mode = retrieve_hits_mode(
            workspace_id=self.workspace_id,
            query=query,
            mode=self.retrieval_mode,
            top_k=top_k,
            doc_ids=self.doc_ids,
        )
        if not hits:
            raise CourseAgentError("No retrieval hits found for this course.")
        return hits, used_mode

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
        used_mode = self.retrieval_mode
        for idx, topic in enumerate(topics, start=1):
            hits, used_mode = self._retrieve_hits(topic, top_k=8)
            batches.append(hits)
            if progress_cb:
                progress_cb(idx, total)

        merged_hits = self._merge_hits(batches)
        bundle = build_citation_bundle(merged_hits)
        prompt, prompt_version = build_prompt(
            "course_overview",
            self.workspace_id,
            context=bundle.numbered_context,
            topics=topics,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CourseAgentError(str(exc)) from exc
        return AgentOutput(
            content=content,
            citations=bundle.citations,
            hits=merged_hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
        )

    def generate_cheatsheet(self, progress_cb: callable | None = None) -> AgentOutput:
        sections = [
            "Definitions",
            "Key Formulas",
            "Typical Question Types",
            "Common Pitfalls",
        ]
        total = len(sections)
        batches = []
        used_mode = self.retrieval_mode
        for idx, section in enumerate(sections, start=1):
            hits, used_mode = self._retrieve_hits(section, top_k=8)
            batches.append(hits)
            if progress_cb:
                progress_cb(idx, total)

        merged_hits = self._merge_hits(batches)
        bundle = build_citation_bundle(merged_hits)
        prompt, prompt_version = build_prompt(
            "course_cheatsheet",
            self.workspace_id,
            context=bundle.numbered_context,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CourseAgentError(str(exc)) from exc
        return AgentOutput(
            content=content,
            citations=bundle.citations,
            hits=merged_hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
        )

    def explain_selection(self, selection: str, mode: str) -> AgentOutput:
        hits, used_mode = self._retrieve_hits(selection, top_k=8)
        bundle = build_citation_bundle(hits)
        prompt, prompt_version = build_prompt(
            "course_explain",
            self.workspace_id,
            selection=selection,
            mode=mode,
            context=bundle.numbered_context,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CourseAgentError(str(exc)) from exc
        return AgentOutput(
            content=content,
            citations=bundle.citations,
            hits=hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
        )
