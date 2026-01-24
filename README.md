# StudyFlow-AI

StudyFlow-AI is a local-first study workspace for PDFs with OCR, coaching, asset versioning, and optional API mode.

## v2.x Highlights
- OCR pipeline (optional) with auto/on/off modes
- Study Coach (two-phase guidance with guard)
- Plugin registry (import/export + citations exporters)
- Prompt registry with versioning + local overrides
- Standardized importers (Zotero, arXiv/DOI/URL, folder sync)
- Concept cards and related work manager
- Workspace bundles and submission packs
- Task queue + benchmarks + embedding cache
- Structured validation + citation checks
- Index maintenance and storage hygiene
- Asset versioning for generated outputs (pin/rollback/diff)
- Optional API mode via FastAPI (local/self-hosted)
- Hybrid retrieval (Vector + BM25) with mode switch

## Quickstart (3 steps)
1) Clone: `git clone https://github.com/li147852xu/studyflow-ai.git`
2) Install: `python -m pip install -e .`
3) Run: `streamlit run app/main.py`

## API Mode (Optional)
1) Start server: `studyflow api serve --host 127.0.0.1 --port 8000`
2) In Settings, switch UI Mode to `api` and set Base URL.
3) (Optional) set `API_TOKEN` and pass `Authorization: Bearer <token>`.

## UI Overview
- Three-column layout: left navigation + collections, center workspace, right inspector.
- Pages: Home, Library, Courses, Papers, Presentations, History, Settings, Help.
- Help entry lives inside the app (open Help in the left navigation).
- Local data lives under `workspaces/<wid>/` (uploads, indexes, runs, outputs).

## Configuration
Create `config.toml` from `config.example.toml`, then set your API key in env:
- `STUDYFLOW_PROFILE` (optional, selects profile)
- `STUDYFLOW_LLM_BASE_URL`, `STUDYFLOW_LLM_MODEL` (optional overrides)
- `STUDYFLOW_EMBED_MODEL` (optional override)
- `STUDYFLOW_LLM_API_KEY` (or the profile `api_key_env`)

The app auto-loads a local `.env` file if present. Do not commit real keys.

## CLI Quickstart
- `studyflow doctor`
- `studyflow workspace create <name>`
- `studyflow ingest --workspace <id> --ocr auto <pdf_path>`
- `studyflow query --workspace <id> --mode bm25 "question"`
- `studyflow gen --workspace <id> --type slides --source <doc_id> --duration 5 --mode bm25`
- `studyflow asset ls --workspace <id>`
- `studyflow asset diff --asset <id> --a <ver> --b <ver>`
- `studyflow api ping --base-url http://127.0.0.1:8000`
- `studyflow coach start --workspace <id> --problem "..."`
- `studyflow coach submit --workspace <id> --session <sid> --answer "..."`
- `studyflow plugins ls`
- `studyflow import folder --workspace <id> --path <folder>`
- `studyflow import zotero --workspace <id> --data-dir <zotero_dir>`
- `studyflow import arxiv --workspace <id> --id 1706.03762`
- `studyflow concepts build --workspace <id> --papers <pid...>`
- `studyflow concepts search --workspace <id> "query"`
- `studyflow related create --workspace <id> --papers <pid...> --topic "..."`
- `studyflow bundle export --workspace <id> --with-pdf`
- `studyflow bundle import --path <bundle.zip>`
- `studyflow pack make --workspace <id> --type slides --source <doc_id>`
- `studyflow tasks ls --workspace <id>`
- `studyflow index status <workspace_id>`
- `studyflow index vacuum <workspace_id>`
- `studyflow clean --workspace <id> --dry-run`

## Using Ingest + Citation Preview
Upload a PDF on any page and the UI will show:
- page count, chunk count, and page range
- a "Show citations preview" button that displays 3 sample citations

## Retrieval Modes
- Vector: embedding retrieval only
- BM25: lexical retrieval only
- Hybrid: fused score (Vector + BM25)

After ingesting, click "Build/Refresh Vector Index" to create the vector index.
Use the Retrieval Mode selector on each page.

## Course Workspace (V0.1)
1) Create/select a course on the Courses page.
2) Upload lecture PDFs and link them to the course (auto-linked on upload).
3) Click "Generate Course Overview" or "Generate Exam Cheatsheet" to produce
   downloadable text with citations.
4) Use "Explain Selection" with the four modes for targeted explanations.

## Paper Library (V0.1.1)
1) Upload paper PDFs on the Papers page.
2) Review/edit metadata and add tags.
3) Generate PAPER_CARD and download as `.txt`.
4) Use the aggregator to synthesize consensus/divergence/routes/related work.

## Presentation Builder (V0.1.2)
1) Go to Presentations and select a source document/paper.
2) Choose duration (3/5/10/20 minutes).
3) Generate the Marp deck, view Q&A and references, download `.md`.

## Concept Cards + Related Work (V2.4)
1) Build concept cards from selected papers or a course.
2) Search cards by keyword and type filters.
3) Create a related work project, then update it as you add new papers.

## Workspace Bundles + Submission Packs (V2.5)
1) Export a bundle to migrate a workspace across machines (optional PDFs/assets).
2) Import a bundle to create a new workspace and rebuild indexes as needed.
3) Generate submission packs for slides/exam/related work from existing assets.

## Performance + Reliability (V2.6)
1) Ingest and index tasks are queued with resume/retry/cancel.
2) Embedding cache avoids recomputing unchanged chunks.
3) Repeatable benchmark scripts output JSON metrics.

## Quality + Reproducibility (V2.7)
1) Run logs and asset versions record full generation metadata.
2) Citation consistency checks flag missing or invalid references.
3) Structured output validation retries once on failure.

## Scalability + Maintenance (V2.8)
1) Index status/rebuild/vacuum CLI keeps vectors and BM25 healthy.
2) `doctor --deep` reports orphans, disk usage, cache, and OCR readiness.
3) `clean` safely removes cache/outputs/exports with dry-run by default.

## Run Logs
Each generation and retrieval chat produces a `run_id` and writes a JSON log to
`workspaces/<wid>/runs/`. The UI shows the run_id and log path after completion.

## UI Guide
- The UI includes a Help page with full workflows and troubleshooting.
- Navigation, workspace management, and status live in the left column.
- History is stored in SQLite and shown in the History page per workspace.
- Coach sessions are stored in SQLite and mirrored to `workspaces/<wid>/coach/`.
- Prompt overrides live in `workspaces/<wid>/prompts_override.json`.

### Persistence
- Workspaces, documents, chunks, history, and UI settings are stored in SQLite.
- Indexes and outputs are derived data in `workspaces/<wid>/`.
- Backup/restore: copy the entire `workspaces/<wid>/` directory.

### Workspace Layout
- `docs/` imported PDFs
- `cache/` embeddings cache (optional)
- `index/` vector + BM25 indexes
- `outputs/` generated exports, packs, benchmarks
- `exports/` bundle exports
- `runs/` run logs
- `logs/` runtime logs
- `history/` UI history snapshots

## Privacy & Storage
- All data stays local by default; API mode is for local/self-hosted use.
- API tokens are read from env only and not stored in the DB.
- OCR requires optional dependencies (tesseract + pytesseract; EasyOCR optional).
- Importers store external source mappings in SQLite and write PDFs to `workspaces/<wid>/docs/`.
- Install tesseract:
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - Windows: `choco install tesseract`

## Cleanup + Verification
Before running version verification, clean local workspaces:
`python scripts/cleanup_workspaces.py`

V0.1 real flow example:
`python scripts/real_flow_v0_1.py`

## Real Flow Check (Optional)
To run a real flow that downloads the "Attention Is All You Need" PDF and calls
the LLM, set `STUDYFLOW_RUN_REAL_FLOW=1` and then run:
`python scripts/verify_v0_0_1.py`

## Disclaimer
You must provide your own API key. The application does not store keys on disk.
