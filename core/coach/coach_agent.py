from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.coach.protocol import requires_guard
from core.prompts.registry import build_prompt
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode


class CoachError(RuntimeError):
    pass


@dataclass
class CoachOutput:
    content: str
    citations: list[str]
    hits: list[Hit]
    retrieval_mode: str
    run_id: str | None = None
    prompt_version: str | None = None


class CoachAgent:
    def __init__(self, workspace_id: str, retrieval_mode: str = "vector") -> None:
        self.workspace_id = workspace_id
        self.retrieval_mode = retrieval_mode

    def _retrieve(self, query: str) -> tuple[list[Hit], str]:
        hits, used_mode = retrieve_hits_mode(
            workspace_id=self.workspace_id,
            query=query,
            mode=self.retrieval_mode,
            top_k=8,
        )
        return hits, used_mode

    def phase_a(self, problem: str) -> CoachOutput:
        if requires_guard(problem):
            content = (
                "I can help with a solution framework and hints, but I won't provide a full final answer. "
                "Please share the problem requirements, and I'll guide you step by step."
            )
            return CoachOutput(content=content, citations=[], hits=[], retrieval_mode="none")

        hits, used_mode = self._retrieve(problem)
        context = ""
        citations = []
        if hits:
            bundle = build_citation_bundle(hits)
            context = bundle.numbered_context
            citations = bundle.citations
        prompt, prompt_version = build_prompt(
            "coach_phase_a",
            self.workspace_id,
            context=context,
            problem=problem,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CoachError(str(exc)) from exc
        return CoachOutput(
            content=content,
            citations=citations,
            hits=hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
        )

    def phase_b(self, problem: str, answer: str) -> CoachOutput:
        if requires_guard(answer):
            content = (
                "I can review your work and give hints, but I won't provide a full final answer. "
                "Please share your attempt so I can help you improve it."
            )
            return CoachOutput(content=content, citations=[], hits=[], retrieval_mode="none")

        query = f"{problem}\n{answer}"
        hits, used_mode = self._retrieve(query)
        context = ""
        citations = []
        if hits:
            bundle = build_citation_bundle(hits)
            context = bundle.numbered_context
            citations = bundle.citations
        prompt, prompt_version = build_prompt(
            "coach_phase_b",
            self.workspace_id,
            context=context,
            problem=problem,
            answer=answer,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise CoachError(str(exc)) from exc
        return CoachOutput(
            content=content,
            citations=citations,
            hits=hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
        )
