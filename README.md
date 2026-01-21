# StudyFlow-AI

StudyFlow-AI is a minimal local workspace UI for uploading PDFs and chatting with an OpenAI-compatible LLM.

## V0.0.1 Features
- Streamlit UI with Courses / Papers / Presentations pages
- Local workspace management backed by SQLite
- PDF upload and save to local workspace folders
- Simple LLM chat (no retrieval, no citations)

## Quickstart (3 steps)
1) Clone: `git clone https://github.com/li147852xu/studyflow-ai.git`
2) Install: `python -m pip install -e .`
3) Run: `streamlit run app/main.py`

## Configuration
Set these environment variables before running:
- `STUDYFLOW_LLM_BASE_URL` (example: `https://api.openai.com/v1`)
- `STUDYFLOW_LLM_API_KEY`
- `STUDYFLOW_LLM_MODEL` (example: `gpt-4o-mini`)
- `STUDYFLOW_WORKSPACES_DIR` (optional, default `./workspaces`)

You can use `.env.example` as a template, but do not commit real keys.
The app auto-loads a local `.env` file if present.

## Real Flow Check (Optional)
To run a real flow that downloads the "Attention Is All You Need" PDF and calls
the LLM, set `STUDYFLOW_RUN_REAL_FLOW=1` and then run:
`python scripts/verify_v0_0_1.py`

## Disclaimer
You must provide your own API key. The application does not store keys on disk.
