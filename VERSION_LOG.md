# VERSION LOG

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
