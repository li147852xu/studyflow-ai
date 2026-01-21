# VERSION LOG

## V0.0.3
- Added vector retrieval modules (embeddings + Chroma)
- Added retrieval service and UI toggle for RAG-lite answers
- Added verify script for vector retrieval
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
