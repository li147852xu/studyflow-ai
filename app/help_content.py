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
        "title": "History & Data Storage",
        "bullets": [
            "History records recent actions, outputs, and citations counts.",
            "Data is stored in workspaces/<wid>/ (uploads, indexes, runs, outputs).",
            "SQLite stores workspace metadata, documents, chunks, and settings.",
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
