# VERSION LOG

## UI Refactor (no version bump)
- Added single-page router with three-column shell and unified navigation
- Added Workflows hub, Tasks/Exports/Diagnostics centers, and in-app Help center
- Added UI facade helpers and UI smoke verification script
- Verification: `python scripts/verify_ui_app.py`, `python -m compileall .`, `pytest -q`, `python -c "import app.main"`

## V2.8
- Added index maintenance CLI (status/rebuild/vacuum) and deep doctor checks
- Added workspace clean command with dry-run safeguards
- Hardened bulk import via task queue integration
- Verification: `python scripts/verify_v2_8.py`, `python -m compileall .`, `pytest -q`

## V2.7
- Added reproducibility metadata to run logs and asset versions
- Added citation consistency checks with user-visible warnings
- Added structured output validation with one retry for key generators

## V2.6
- Added task queue with resume/retry/cancel and task-based ingest/index
- Added embedding cache + batch/concurrent embeddings with streaming indexing
- Added benchmark scripts for ingest/query

## V2.5
- Added workspace bundle export/import with sanitized manifests
- Added submission packs (slides/exam/related) with manifests
- Added bundle/pack CLI commands and verify_v2_5.py
- Verification: `python scripts/verify_v2_5.py`, `python -m compileall .`, `pytest -q`, `studyflow bundle export/import`, `studyflow pack make`

## V2.4
- Added concept cards with evidence and incremental processing markers
- Added related work manager with outline/draft export and asset versions
- Added concepts/related CLI commands and verify_v2_4.py
- Verification: `python scripts/verify_v2_4.py`, `python -m compileall .`, `pytest -q`, `studyflow concepts build/search`, `studyflow related create/update/export`

## V2.3
- Added standardized importers for Zotero, arXiv/DOI/URL, and folder sync
- Added external_sources/external_mappings tables and document source metadata
- Added import CLI commands and verify_v2_3.py
- Verification: `python scripts/verify_v2_3.py`, `python -m compileall .`, `pytest -q`, `studyflow doctor`, `studyflow import folder`, `studyflow import zotero`, `studyflow import arxiv`

## V2.2
- Added plugin registry with importer/exporter and prompt registry with overrides
- Added coach API endpoints and plugins/prompts endpoints
- Added verify_v2_2.py and v2.2 verification flow
- Verification: `python scripts/verify_v2_2.py`, `python -m compileall .`, `pytest -q`, `studyflow doctor`, `studyflow workspace create`, `studyflow ingest --ocr auto`, `studyflow query`, `studyflow gen`, `studyflow coach start/submit`, `studyflow plugins ls/run`

## V2.1
- Added Study Coach with two-phase protocol and guard
- Added coach session storage (SQLite + local JSON)
- Added coach CLI + UI
- Verification: `pytest -q`, `python -m compileall .`, `studyflow coach start`, `studyflow coach submit`

## V2.0
- Added OCR pipeline with auto/on/off modes (optional dependencies)
- Added page-level metadata, image counts, and OCR source tracking
- Added OCR settings in UI and CLI ingest options
- Verification: `pytest -q`, `python -m compileall .`, `studyflow ingest --ocr auto`

## V1.3
- Added release-grade CLI commands for API serve/ping and asset management
- Added verify_v1_3.py for full validation pipeline
- Updated README for v1.x features, API mode, and CLI usage
- Verification: `python scripts/verify_v1_3.py`, `python -m compileall .`, `pytest -q`, `studyflow doctor`, `studyflow workspace create`, `studyflow ingest`, `studyflow query`, `studyflow gen`, `studyflow asset ls/show/pin/rollback/diff/export-citations`

## V1.2
- Added FastAPI service mode with token auth
- Added UI Direct/API mode switch and API base URL setting
- Added API endpoints for ingest/query/generate/assets
- Verification: `pytest -q`, `python -m compileall .`, `python -m cli.main api ping`, `python -c "from backend.api import app"`

## V1.1
- Added asset versioning with pin/rollback and diff
- Added citations export (JSON + TXT) for assets
- Added asset CLI commands and tests for versioning/diff
- Verification: `pytest -q`, `python -m compileall .`, `python -m cli.main asset ls`

## V1.0
- Added config profiles and model presets (config.toml)
- Added incremental indexing and workspace/document CLI management
- Added CLI (doctor/ingest/query/gen/index)
- Added pytest unit tests + minimal e2e
- UI/UX polish (no version bump): unified sidebar, Help/Docs, history/settings
- UI refactor (no version bump): single-page router, three-column layout, componentized views
- Verification: `python scripts/verify_ui_refactor.py`, `python -m compileall .`, `pytest -q`, `studyflow doctor`, `studyflow workspace create`, `studyflow ingest`, `studyflow query`, `studyflow gen`, `python scripts/verify_v1_0.py`, `python scripts/verify_ui_polish.py`, `python -c "import app.main"`, `streamlit run app/main.py --server.headless true`

## V0.2
- Added BM25 index and hybrid retrieval fusion
- Added retrieval modes and workspace filtering
- Added run logs with run_id
- Verification: `python scripts/verify_v0_2.py`, `python -m compileall .`, `streamlit run app/main.py --server.headless true`

## V0.1.2
- Added SlidesAgent and Presentation Builder UI
- Added Marp deck generation with speaker notes, Q&A, and references
- Added V0.1.2 verification
- Verification: `python scripts/verify_v0_1_2.py`, `python -m compileall .`, `streamlit run app/main.py --server.headless true`

## V0.1.1
- Added papers tables with metadata and tags
- Added paper metadata extraction and editable metadata in UI
- Added PAPER_CARD generation and cross-paper aggregator
- Added verification for paper library flow
- Verification: `python scripts/verify_v0_1_1.py`, `python -m compileall .`, `streamlit run app/main.py --server.headless true`

## V0.1
- Added course workspace (courses + course_documents tables)
- Added CourseAgent for overview/cheatsheet generation with citations
- Added explain_selection tool with four modes
- Added V0.1 verification and real flow scripts
- Verification: `python scripts/verify_v0_1.py`, `python -m compileall .`, `streamlit run app/main.py --server.headless true`

## V0.0.3
- Added vector retrieval modules (embeddings + Chroma)
- Added retrieval service and UI toggle for RAG-lite answers
- Added verify script for vector retrieval
- Added workspace cleanup and real-flow script for V0.0.3
- Verification: `python scripts/verify_v0_0_3.py`, `python -m compileall .`, `streamlit run app/main.py --server.headless true`

## V0.0.2
- Added PDF ingest with page-aware chunking (900/150 overlap)
- Added chunks table and document metadata (sha256, page_count)
- Added citation preview (filename + page number + snippet)
- Verification: `python scripts/verify_v0_0_2.py`, `python -m compileall .`, `streamlit run app/main.py --server.headless true`

## V0.0.1
- Added Streamlit UI with Courses/Papers/Presentations pages
- Implemented local workspace management with SQLite
- Added PDF upload/save to workspace folders
- Added OpenAI-compatible LLM chat (no retrieval)
- Added optional real flow check that downloads the Attention Is All You Need PDF
- Auto-loads local `.env` for configuration
- Verification: `python scripts/verify_v0_0_1.py` (set `STUDYFLOW_RUN_REAL_FLOW=1` to enable real flow), `python -m compileall .`, `streamlit run app/main.py --server.headless true`
