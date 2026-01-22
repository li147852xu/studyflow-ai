# StudyFlow-AI

StudyFlow-AI is a minimal local workspace UI for uploading PDFs, ingesting text with citations, and completing course/paper/presentation workflows with retrieval.

## V0.1.2 Features
- Presentation Builder with Marp deck generation (3/5/10/20 min)
- Speaker notes + Q&A list + references with citations
- Paper library with metadata extraction (title/authors/year) and tags
- PAPER_CARD generation with citations
- Cross-paper aggregation with citations (consensus/divergence/routes/related work)
- Paper library with metadata extraction (title/authors/year) and tags
- PAPER_CARD generation with citations
- Cross-paper aggregation with citations (consensus/divergence/routes/related work)
- Course workspace with course creation and lecture PDF linking
- One-click COURSE_OVERVIEW and EXAM_CHEATSHEET generation with citations
- Explain selection tool (plain/example/pitfall/link_prev)
- Vector retrieval with Chroma over chunked text
- Local embeddings via `sentence-transformers`
- PDF ingest with page-aware chunking (900/150)
- SQLite storage for documents and chunks with citations
- Citation preview with filename + page number + snippet
- Streamlit UI with Courses / Papers / Presentations pages
- Local workspace management backed by SQLite
- PDF upload and save to local workspace folders
- Simple LLM chat (no retrieval)

## Quickstart (3 steps)
1) Clone: `git clone https://github.com/li147852xu/studyflow-ai.git`
2) Install: `python -m pip install -e .`
3) Run: `streamlit run app/main.py`

## Configuration
Set these environment variables before running:
- `STUDYFLOW_LLM_BASE_URL` (example: `https://api.openai.com/v1`)
- `STUDYFLOW_LLM_API_KEY`
- `STUDYFLOW_LLM_MODEL` (example: `gpt-4o-mini`)
- `STUDYFLOW_EMBED_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`)
- `STUDYFLOW_WORKSPACES_DIR` (optional, default `./workspaces`)

You can use `.env.example` as a template, but do not commit real keys.
The app auto-loads a local `.env` file if present.

## Using Ingest + Citation Preview
Upload a PDF on any page and the UI will show:
- page count, chunk count, and page range
- a "Show citations preview" button that displays 3 sample citations

## Using Vector Retrieval (V0.1.1)
After ingesting, click "Build/Refresh Vector Index" to create the vector index.
In Chat, toggle "Use Retrieval (V0.0.3)" to see retrieval hits and citations.

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
