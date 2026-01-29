from __future__ import annotations

from dataclasses import dataclass

from core.formatting.citations import build_citation_bundle
from core.prompts.registry import build_prompt
from core.quality.validators import validate_paper_card
from core.retrieval.retriever import Hit
from service.chat_service import ChatConfigError, chat
from service.retrieval_service import retrieve_hits_mode


class PaperAgentError(RuntimeError):
    pass


@dataclass
class PaperCardOutput:
    content: str
    citations: list[str]
    hits: list[Hit]
    retrieval_mode: str
    warnings: list[str] | None = None
    run_id: str | None = None
    asset_id: str | None = None
    asset_version_id: str | None = None
    asset_version_index: int | None = None
    prompt_version: str | None = None


class PaperAgent:
    def __init__(self, workspace_id: str, doc_id: str, retrieval_mode: str) -> None:
        self.workspace_id = workspace_id
        self.doc_id = doc_id
        self.retrieval_mode = retrieval_mode

    def generate_paper_card(self, progress_cb: callable | None = None) -> PaperCardOutput:
        queries = [
            "paper summary",
            "key contributions",
            "strengths weaknesses",
            "extension ideas",
        ]
        batches: list[list[Hit]] = []
        total = len(queries)
        used_mode = self.retrieval_mode
        for idx, query in enumerate(queries, start=1):
            hits, used_mode = retrieve_hits_mode(
                workspace_id=self.workspace_id,
                query=query,
                mode=self.retrieval_mode,
                top_k=8,
                doc_ids=[self.doc_id],
            )
            if not hits:
                raise PaperAgentError("No retrieval hits for paper.")
            batches.append(hits)
            if progress_cb:
                progress_cb(idx, total)

        merged_hits = _merge_hits(batches)
        bundle = build_citation_bundle(merged_hits)
        prompt, prompt_version = build_prompt(
            "paper_card",
            self.workspace_id,
            context=bundle.numbered_context,
        )
        try:
            content = chat(prompt=prompt, temperature=0.2)
        except ChatConfigError as exc:
            raise PaperAgentError(str(exc)) from exc
        warnings: list[str] | None = None
        valid, error = validate_paper_card(content)
        if not valid:
            retry_prompt = (
                prompt
                + "\n\nIMPORTANT: Use EXACTLY these section headers (one per line):\n"
                "Summary:\n(your summary paragraph)\n\n"
                "Contributions:\n- point 1\n- point 2\n\n"
                "Strengths:\n- point 1\n- point 2\n\n"
                "Weaknesses:\n- point 1\n- point 2\n\n"
                "Extensions:\n- point 1\n- point 2"
            )
            try:
                retry_content = chat(prompt=retry_prompt, temperature=0.1)
            except ChatConfigError as exc:
                raise PaperAgentError(str(exc)) from exc
            valid, error = validate_paper_card(retry_content)
            if valid:
                content = retry_content
            else:
                # Keep original LLM output but add warning
                warnings = [
                    "Output format may not be perfectly structured. Content is still based on the paper."
                ]
        return PaperCardOutput(
            content=content,
            citations=bundle.citations,
            hits=merged_hits,
            retrieval_mode=used_mode,
            prompt_version=prompt_version,
            warnings=warnings,
        )


def _merge_hits(batches: list[list[Hit]]) -> list[Hit]:
    seen = set()
    merged = []
    for batch in batches:
        for hit in batch:
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            merged.append(hit)
    return merged
