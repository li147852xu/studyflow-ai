from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import requests

from service.course_service import explain_selection, generate_cheatsheet, generate_overview
from service.ingest_service import ingest_document
from service.paper_generate_service import aggregate_papers, generate_paper_card
from service.paper_service import ingest_paper
from service.presentation_service import generate_slides
from service.retrieval_service import answer_with_retrieval


class ApiModeError(RuntimeError):
    pass


@dataclass
class TextGenerationResult:
    content: str
    citations: list[str]
    run_id: str | None
    asset_id: str | None
    asset_version_id: str | None
    asset_version_index: int | None


@dataclass
class SlidesGenerationResult:
    deck: str
    qa: list[str]
    citations: list[str]
    run_id: str | None
    asset_id: str | None
    asset_version_id: str | None
    asset_version_index: int | None


@dataclass
class QueryResult:
    answer: str
    hits: list[dict]
    citations: list[str]
    run_id: str | None


class ApiModeAdapter:
    def __init__(self, mode: str, base_url: str) -> None:
        self.mode = mode
        self.base_url = base_url.rstrip("/")
        self.token = os.getenv("API_TOKEN", "")

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        except requests.RequestException as exc:
            raise ApiModeError(f"API request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise ApiModeError(f"API error {resp.status_code}: {resp.text}")
        return resp.json()

    def ingest(
        self,
        *,
        workspace_id: str,
        filename: str,
        data: bytes,
        save_dir,
        kind: str = "document",
        ocr_mode: str = "off",
        ocr_threshold: int = 50,
        doc_type: str = "other",
    ) -> dict:
        if self.mode == "direct":
            if kind == "paper":
                paper_id, metadata = ingest_paper(
                    workspace_id=workspace_id,
                    filename=filename,
                    data=data,
                    save_dir=save_dir,
                    ocr_mode=ocr_mode,
                    ocr_threshold=ocr_threshold,
                )
                return {
                    "paper_id": paper_id,
                    "title": metadata.title,
                    "authors": metadata.authors,
                    "year": metadata.year,
                }
            result = ingest_document(
                workspace_id=workspace_id,
                filename=filename,
                data=data,
                save_dir=save_dir,
                ocr_mode=ocr_mode,
                ocr_threshold=ocr_threshold,
                doc_type=doc_type,
            )
            return result.__dict__
        payload = {
            "workspace_id": workspace_id,
            "filename": filename,
            "data_base64": base64.b64encode(data).decode("utf-8"),
            "kind": kind,
            "ocr_mode": ocr_mode,
            "ocr_threshold": ocr_threshold,
            "doc_type": doc_type,
        }
        return self._post("/ingest", payload)

    def query(self, *, workspace_id: str, query: str, mode: str, top_k: int = 8) -> QueryResult:
        if self.mode == "direct":
            answer, hits, citations, run_id = answer_with_retrieval(
                workspace_id=workspace_id, query=query, mode=mode, top_k=top_k
            )
            return QueryResult(
                answer=answer,
                hits=[hit.__dict__ for hit in hits],
                citations=citations,
                run_id=run_id,
            )
        payload = {"workspace_id": workspace_id, "query": query, "mode": mode, "top_k": top_k}
        data = self._post("/query", payload)
        return QueryResult(
            answer=data["answer"],
            hits=data.get("hits", []),
            citations=data.get("citations", []),
            run_id=data.get("run_id"),
        )

    def generate(self, *, action_type: str, payload: dict) -> TextGenerationResult | SlidesGenerationResult:
        if self.mode == "direct":
            if action_type == "course_overview":
                output = generate_overview(**payload)
                return TextGenerationResult(
                    content=output.content,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            if action_type == "course_cheatsheet":
                output = generate_cheatsheet(**payload)
                return TextGenerationResult(
                    content=output.content,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            if action_type == "course_explain":
                output = explain_selection(**payload)
                return TextGenerationResult(
                    content=output.content,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            if action_type == "course_qa":
                from service.course_service import answer_course_question
                output = answer_course_question(**payload)
                return TextGenerationResult(
                    content=output.content,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            if action_type == "paper_card":
                output = generate_paper_card(**payload)
                return TextGenerationResult(
                    content=output.content,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            if action_type == "paper_aggregate":
                output = aggregate_papers(**payload)
                return TextGenerationResult(
                    content=output.content,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            if action_type == "slides":
                output = generate_slides(**payload)
                return SlidesGenerationResult(
                    deck=output.deck,
                    qa=output.qa,
                    citations=output.citations,
                    run_id=output.run_id,
                    asset_id=output.asset_id,
                    asset_version_id=output.asset_version_id,
                    asset_version_index=output.asset_version_index,
                )
            raise ApiModeError("Unknown action type.")

        safe_payload = {key: value for key, value in payload.items() if not callable(value)}
        data = self._post("/generate", {"action_type": action_type, **safe_payload})
        if action_type == "slides":
            return SlidesGenerationResult(
                deck=data["deck"],
                qa=data.get("qa", []),
                citations=data.get("citations", []),
                run_id=data.get("run_id"),
                asset_id=data.get("asset_id"),
                asset_version_id=data.get("asset_version_id"),
                asset_version_index=data.get("asset_version_index"),
            )
        return TextGenerationResult(
            content=data["content"],
            citations=data.get("citations", []),
            run_id=data.get("run_id"),
            asset_id=data.get("asset_id"),
            asset_version_id=data.get("asset_version_id"),
            asset_version_index=data.get("asset_version_index"),
        )
