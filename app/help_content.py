HELP_SECTIONS = [
    {
        "title": "Quickstart",
        "expanded": True,
        "bullets": [
            "Create or select a workspace on the left.",
            "Upload PDFs in Library or within a workbench.",
            "Build the vector index if you plan to use Vector/Hybrid retrieval.",
            "Open a workbench to generate outputs or use Chat.",
        ],
        "code": "streamlit run app/main.py",
    },
    {
        "title": "Importing PDFs",
        "bullets": [
            "Use Library to ingest one or multiple PDFs.",
            "Each upload extracts text, chunks it, and stores metadata in SQLite.",
            "Re-ingesting the same file hash is skipped automatically.",
            "OCR modes: off, auto (low-text pages), on (all pages).",
        ],
    },
    {
        "title": "Indexing & Retrieval Modes",
        "bullets": [
            "Vector: embeddings-based semantic search.",
            "BM25: lexical match without embeddings.",
            "Hybrid: fused scores from Vector + BM25.",
            "Vector index is built on demand per workspace.",
        ],
    },
    {
        "title": "Workbenches",
        "bullets": [
            "Courses: generate COURSE_OVERVIEW, EXAM_CHEATSHEET, and explain selections.",
            "Papers: generate PAPER_CARD and aggregate questions across papers.",
            "Presentations: generate Marp decks and Q&A lists.",
        ],
    },
    {
        "title": "Study Coach",
        "bullets": [
            "Phase A: framework, key concepts, and pitfalls.",
            "Phase B: review your answer with hints and rubric.",
            "Coach avoids giving full final answers by default.",
        ],
    },
    {
        "title": "Plugins",
        "bullets": [
            "Importer: batch ingest PDFs from a folder.",
            "Exporter: export assets to folders and citations.",
        ],
    },
    {
        "title": "Prompt Overrides",
        "bullets": [
            "Override prompts with workspaces/<wid>/prompts_override.json.",
            "Use prompt_version in Settings to select versions.",
        ],
    },
    {
        "title": "Asset Versions",
        "bullets": [
            "Every generation creates a new asset version.",
            "Use the Inspector to preview, pin, or compare versions.",
            "Export citations as JSON/TXT from the Inspector.",
        ],
    },
    {
        "title": "API Mode",
        "bullets": [
            "Switch UI Mode to API in Settings and provide Base URL.",
            "API mode calls FastAPI endpoints for ingest/query/generate.",
            "Set API_TOKEN for optional bearer auth.",
        ],
    },
    {
        "title": "History & Data Storage",
        "bullets": [
            "History records recent actions, outputs, and citations counts.",
            "Data is stored in workspaces/<wid>/ (uploads, indexes, runs, outputs).",
            "SQLite stores workspace metadata, documents, chunks, and settings.",
            "Coach sessions stored in SQLite and mirrored to workspaces/<wid>/coach/.",
        ],
    },
    {
        "title": "Troubleshooting",
        "bullets": [
            "Missing LLM Base URL/Model/Key: set in Settings or env variables.",
            "Embedding model missing: set STUDYFLOW_EMBED_MODEL or switch to BM25.",
            "Index not built: click Build/Refresh Vector Index in Library.",
            "Parse failed: ensure PDFs are not encrypted and contain text layers.",
        ],
    },
]
