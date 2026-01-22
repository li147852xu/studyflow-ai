HELP_TEXT = """
# StudyFlow-AI Help / Docs

## Quickstart
1) Create or select a workspace in the sidebar.
2) Upload PDFs in Courses/Papers/Presentations.
3) Build Vector Index if you plan to use Vector/Hybrid retrieval.
4) Run generation actions or chat with retrieval.

## Workspace Concept
- Each workspace is a logical container for documents, indexes, and run logs.
- You can create, rename, or delete workspaces in the sidebar.

## PDF Ingest Flow
1) Upload PDF.
2) The app extracts text, splits into chunks, and stores metadata in SQLite.
3) If the same file hash is ingested again, it is skipped.

### PDF Issues
- Encrypted PDF: cannot parse. Use an unlocked copy.
- Scanned PDF: no text layer. Use OCR before upload.
- Empty PDF: ingestion will fail with a clear error.

## Retrieval Modes and Indexing
- Vector: uses embeddings (requires embedding model).
- BM25: lexical search only.
- Hybrid: fused score of BM25 + Vector.

Vector index must be built once per workspace (Build/Refresh Vector Index).
BM25 index is created automatically on ingest and can be rebuilt.

## Courses Workflow
1) Create/select a course.
2) Upload lecture PDFs.
3) Generate Course Overview or Exam Cheatsheet.
4) Use Explain Selection for targeted explanations.

## Papers Workflow
1) Upload papers.
2) Check metadata and tags.
3) Generate PAPER_CARD.
4) Aggregate multiple papers with a question.

## Presentations Workflow
1) Select a source document.
2) Choose duration (3/5/10/20).
3) Generate Marp deck + Q&A.

## Common Errors & Fixes
- Missing LLM Base URL/Model/Key: set in sidebar or config.toml.
- Embedding model missing: set STUDYFLOW_EMBED_MODEL or use BM25.
- Index not built: click Build/Refresh Vector Index.
- Parse failed: verify PDF is not encrypted and has text layer.

## Data Storage & Persistence
- SQLite stores workspace metadata, documents, chunks, and history.
- Indexes live in workspaces/<wid>/index/ and are rebuildable.
- Run logs live in workspaces/<wid>/runs/.
- Outputs live in workspaces/<wid>/outputs/.

### History & Settings
- History records recent actions with a short preview.
- Settings store last workspace and retrieval mode.
- History can be cleared per workspace from sidebar.

## Backup & Migration
- To backup a workspace: copy workspaces/<wid>/ directory.
- To reset: delete workspaces/<wid>/ (you can recreate later).
"""
