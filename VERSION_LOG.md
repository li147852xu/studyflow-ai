# VERSION LOG

## V2.10.0 (2026-01-29) — Release-Grade Distribution & Usability

**Goal**: Transform v2.9 into a polished, externally releasable version with one-click deployment, CI quality gates, comprehensive documentation, and 10-minute time-to-first-value.

### A) Docker & One-Click Startup

- **Dockerfile**: Multi-stage build with Python 3.11, Tesseract OCR, and all dependencies
- **docker-compose.yml**: Single command deployment with persistent volumes
- **Ports**: UI on 8501, API on 8000
- **Environment**: All config via environment variables, no secrets in images
- **Health checks**: Built-in container health monitoring

```bash
# Quick start
docker compose up --build
# Open http://localhost:8501
```

### B) GitHub Actions CI

- **ci.yml**: Automated testing on push/PR to main
- **Quality gates**:
  - `python -m compileall .` — Syntax check
  - `ruff check .` — Linting (pycodestyle, pyflakes, isort, bugbear, pyupgrade)
  - `pytest -q` — Unit tests
  - Import smoke tests for app.main, cli.main, backend.api
- **Docker CI**: Automated Docker build verification
- **Python versions**: 3.10 and 3.11 matrix

### C) README & Documentation

- **Complete rewrite** of README.md with:
  - Clear value proposition and 5 key benefits
  - Quick Start (Docker, 3 steps)
  - 10-Minute Tutorial (5 steps to first output)
  - Feature Map organized by user workflow
  - Configuration guide (env vars, config.toml, retrieval modes, OCR)
  - CLI Reference with all commands
  - Troubleshooting table with common issues and solutions
  - Architecture diagram and component overview
  - Privacy & Local-First section
  - Roadmap (5 items)
  - Contributing guide

- **UI Help content** (app/help_content.py):
  - Aligned with README structure
  - English and Chinese translations
  - Searchable sections with code examples
  - Troubleshooting guides

### D) Usability & 10-Minute TTFV

- **Start Page improvements**:
  - Setup Checklist with LLM, Retrieval, OCR, Workspace status
  - **Load Demo Data** button — one-click sample import
  - **Run Doctor** button — quick diagnostics access
  - Three-button layout: Settings, Demo, Doctor

- **Demo Data**:
  - `examples/ml_fundamentals.pdf` — 4-page ML introduction
  - `scripts/create_demo_pdf.py` — Demo PDF generator
  - Auto-triggers ingest + index on load

- **Error Self-Recovery**:
  - All error states show actionable buttons
  - Run Doctor, Retry Task, Rebuild Index options
  - User-readable error messages with next steps

- **Background Tasks**:
  - Page navigation allowed during tasks
  - Write operations locked with clear indicator
  - Task progress visible in Tasks center

### E) Stability & Performance

- **Ruff linting**: All code passes ruff check with sensible rules
- **Code cleanup**: Fixed unused imports, variables, and type hints
- **pyproject.toml**: Added ruff, pytest configuration
- **.gitignore**: Comprehensive coverage of all runtime artifacts

### Verification

```bash
# Full release verification
python scripts/verify_release_v2_10.py

# Individual checks
python -m compileall .
ruff check .
pytest -q
python -c "import app.main"
docker compose build
```

### File Changes

**New files**:
- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `scripts/verify_release_v2_10.py`
- `scripts/create_demo_pdf.py`
- `examples/ml_fundamentals.pdf`

**Modified files**:
- `pyproject.toml` — Version 2.10.0, ruff config, pytest config
- `README.md` — Complete rewrite
- `.gitignore` — Expanded coverage
- `app/help_content.py` — Aligned with README
- `app/ui/pages_start.py` — Load Demo Data, Run Doctor buttons
- `app/ui/i18n.py` — New translation keys

---

## V2.9 (2026-01-27)
### New Features
- **Document Summaries**: LLM-generated one-line descriptions for documents
  - Auto-generate or manual generation via Library document details
  - Display summaries in document list for quick reference
- **Knowledge Q&A for Courses**: Ask questions about course content
  - New "Knowledge Q&A" section in Course generation
  - Answers based on linked course materials with citations
- **Coach Session Management**: Named sessions with full history
  - Sessions auto-named (会话 1, 会话 2) or custom naming
  - Session rename functionality
  - Display session names instead of UUIDs
- **Enhanced Library Filtering**: Course-based document grouping
  - Filter course docs by specific course
  - "Uncategorized course docs" option for unlinked documents
- **Per-Module Output Display**: Separated progress and outputs
  - Each Create tab shows only its own generation tasks
  - Independent latest output display per module

### UI Improvements
- Restructured Course generation Step 3 with expanders
- Added help text for all generation options
- Cleaner session selection in Study Coach

### Code Changes
- Added `summary` column to documents table
- Added `name` column to coach_sessions table
- New `service/summary_service.py` for summary generation
- New `answer_course_question` function in course_service
- Updated `_latest_generate_task` with type_prefix filtering

### Documentation
- Updated Help content (English and Chinese)
- Professional README redesign for GitHub

---

## V2.8.x (UI + persistence polish)
- Added required doc_type (course/paper/other) across ingest, storage, retrieval filtering
- Start page setup checklist + quick-entry cards with settings-first flow
- Background tasks with write locks, exit confirmation, and recent activity history (max 30)
- Recent Activity tab with output viewing + download/export shortcuts
- Verification: `python scripts/verify_ui_app_v2_9.py`, `python -m compileall .`, `pytest -q`, `python -c "import app.main"`

## UI Refresh (light, app-like; no version bump)
- Added light theme and simplified Start/Library/Create/Tools navigation
- Added auto-processing import flows with task-aware refresh
- Added right-side inspector and new UI facade helpers
- Verification: `python scripts/verify_ui_app_v2.py`, `python -m compileall .`, `pytest -q`, `python -c "import app.main"`

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
