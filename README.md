# StudyFlow AI

**Your AI-powered, local-first study workspace for PDFs.**

Transform how you study and research: import PDFs, get intelligent summaries, generate structured study materials, and receive personalized coaching—all while keeping your data private on your own machine.

---

## Why StudyFlow AI?

- **Privacy-First**: All data stays local. Your API keys are never stored on disk.
- **Cited Outputs**: Every generated answer includes traceable references to source pages.
- **Structured Assets**: Course overviews, paper cards, slides—all versioned and exportable.
- **10-Minute Value**: Load demo data → generate your first output → export with citations.
- **Extensible**: Plugin system for custom importers/exporters; CLI + API for automation.

---

## Table of Contents

- [Quick Start (Docker)](#quick-start-docker)
- [10-Minute Tutorial](#10-minute-tutorial)
- [Feature Map](#feature-map)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Privacy & Local-First](#privacy--local-first)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Quick Start (Docker)

The fastest way to run StudyFlow AI:

```bash
# 1. Clone the repository
git clone https://github.com/li147852xu/studyflow-ai.git
cd studyflow-ai

# 2. (Optional) Set your LLM API key in environment
export STUDYFLOW_LLM_BASE_URL=https://api.openai.com/v1
export STUDYFLOW_LLM_API_KEY=sk-your-key
export STUDYFLOW_LLM_MODEL=gpt-4

# 3. Start with Docker Compose
docker compose up --build

# 4. Open your browser
# UI: http://localhost:8501
# API: http://localhost:8000 (if needed)
```

**No Docker?** Install locally:

```bash
pip install -e .
streamlit run app/main.py
```

---

## 10-Minute Tutorial

Get value from StudyFlow AI in just a few steps:

### Step 1: Launch

```bash
docker compose up --build
# Open http://localhost:8501
```

### Step 2: Configure LLM (if not set via environment)

1. Go to **Tools → Settings**
2. Enter your LLM Base URL (e.g., `https://api.openai.com/v1`)
3. Enter your Model name (e.g., `gpt-4` or `deepseek-chat`)
4. Enter your API Key
5. Click **Save Settings**

### Step 3: Load Demo Data

1. Go to **Start** page
2. Click **Load Demo Data** (loads sample ML fundamentals PDF)
3. Wait for automatic processing (ingest + index)

### Step 4: Generate Your First Output

1. Go to **Create → Course**
2. Select or create a course (e.g., "ML Intro")
3. Link the demo document to the course
4. Click **Generate Course Overview**
5. View the generated content with citations!

### Step 5: Export

1. Go to **Tools → Recent Activity**
2. Find your generated output
3. Click **Export Pack** to download slides, citations, and metadata

---

## Feature Map

### Start Page
- **Setup Checklist**: Verify LLM, retrieval mode, OCR, and workspace status
- **Quick Actions**: One-click navigation to Import, Ask, and Create
- **Recent Activity**: View last 10 operations with quick access

### Library
- **Import Sources**: Upload PDFs, Zotero, arXiv, DOI, URL, or folder sync
- **Document Types**: Organize as Course, Paper, or Other
- **Auto-Processing**: Imports trigger automatic chunking and indexing
- **Document Summaries**: LLM-generated one-line descriptions

### Create
| Tab | What it generates |
|-----|-------------------|
| **Course** | Course Overview, Exam Cheatsheet, Knowledge Q&A, Explain Selection |
| **Paper** | Paper Card (structured analysis), Multi-Paper Aggregation |
| **Presentation** | Marp slides (1-30 min), Q&A lists, speaker notes |

### Tools
| Tab | Purpose |
|-----|---------|
| **Coach** | Two-phase study guidance (Framework → Review) |
| **Tasks** | Background task queue with progress tracking |
| **Settings** | LLM config, OCR, retrieval mode, language |
| **Diagnostics** | Doctor checks, index rebuild, cleanup |
| **Recent Activity** | History with output viewing and export |

### Help
- In-app documentation with searchable sections
- Troubleshooting guides
- Keyboard shortcuts reference

---

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required for generation features
STUDYFLOW_LLM_BASE_URL=https://api.openai.com/v1
STUDYFLOW_LLM_API_KEY=sk-your-key
STUDYFLOW_LLM_MODEL=gpt-4

# Optional: Embedding model (defaults to local sentence-transformers)
STUDYFLOW_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: OCR settings
STUDYFLOW_OCR_MODE=off    # off | auto | on
STUDYFLOW_OCR_THRESHOLD=50

# Optional: Data directory
STUDYFLOW_WORKSPACES_DIR=./workspaces
```

### Config File (Advanced)

For multiple profiles, create `config.toml`:

```toml
[profiles.default]
llm_base_url = "https://api.openai.com/v1"
llm_model = "gpt-4"
api_key_env = "OPENAI_API_KEY"

[profiles.deepseek]
llm_base_url = "https://api.deepseek.com/v1"
llm_model = "deepseek-chat"
api_key_env = "DEEPSEEK_API_KEY"
```

### Retrieval Modes

| Mode | Description | When to use |
|------|-------------|-------------|
| **Vector** | Semantic search via embeddings | Best for conceptual queries |
| **BM25** | Keyword-based lexical search | Best for exact term matching |
| **Hybrid** | Fused Vector + BM25 scores | Best overall accuracy |

### OCR Setup (Optional)

For scanned PDFs, install Tesseract:

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
choco install tesseract
```

Then set `STUDYFLOW_OCR_MODE=auto` to automatically OCR low-text pages.

---

## CLI Reference

```bash
# System health check
studyflow doctor
studyflow doctor --deep  # Extended checks

# Workspace management
studyflow workspace create "My Project"
studyflow workspace list

# Document ingestion
studyflow ingest --workspace <id> --ocr auto document.pdf

# Build/manage indexes
studyflow index build --workspace <id>
studyflow index status --workspace <id>
studyflow index vacuum --workspace <id>

# Query documents
studyflow query --workspace <id> --mode hybrid "your question"

# Generate content
studyflow gen --workspace <id> --type course_overview --source <course_id>
studyflow gen --workspace <id> --type slides --source <doc_id>

# Study coaching
studyflow coach start --workspace <id> --problem "Explain backpropagation"
studyflow coach submit --session <id> --answer "..."

# Asset management
studyflow asset ls --workspace <id>
studyflow asset diff --id <asset_id> -a <v1> -b <v2>
studyflow asset export-citations --id <asset_id> --version <v>

# Export/Import bundles
studyflow bundle export --workspace <id> --output backup.zip
studyflow bundle import backup.zip

# Task management
studyflow tasks list --workspace <id>
studyflow tasks run <task_id>

# Cleanup
studyflow clean --workspace <id> --dry-run
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **"LLM not configured"** | Go to Settings and enter Base URL, Model, and API Key |
| **Generation buttons disabled** | Check Setup Checklist on Start page; configure missing items |
| **"Embedding model not found"** | Set `STUDYFLOW_EMBED_MODEL` or switch to BM25 retrieval mode |
| **Index not building** | Run `studyflow index build --workspace <id>` or click Rebuild in Diagnostics |
| **OCR not working** | Install Tesseract and set `STUDYFLOW_OCR_MODE=auto` |
| **API error 503** | If using API mode, ensure backend is running: `studyflow api serve` |

### Diagnostic Commands

```bash
# Full system check
studyflow doctor --deep

# Rebuild corrupted index
studyflow index build --workspace <id>

# Vacuum and optimize
studyflow index vacuum --workspace <id>

# Preview cleanup (safe)
studyflow clean --workspace <id> --dry-run

# Force cleanup
studyflow clean --workspace <id>
```

### Error Self-Recovery

When errors occur in the UI:
1. Look for **Run Doctor** button → diagnoses system issues
2. Look for **Retry Task** button → retries failed background tasks
3. Look for **Rebuild Index** button → fixes index corruption

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │  Start  │ │ Library │ │ Create  │ │  Tools  │ │ Help  │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └───────┘ │
└───────┼──────────┼──────────┼──────────┼────────────────────┘
        │          │          │          │
┌───────▼──────────▼──────────▼──────────▼────────────────────┐
│                     Service Layer                           │
│  ingest_service │ retrieval_service │ *_service (agents)   │
└───────┬──────────────────────────────────────┬──────────────┘
        │                                      │
┌───────▼──────────────────────┐  ┌───────────▼───────────────┐
│         Core Modules         │  │      External APIs        │
│  ┌─────────┐ ┌────────────┐  │  │  ┌──────────────────────┐ │
│  │ Chunker │ │ Embedder   │  │  │  │ OpenAI-compatible    │ │
│  │ (ingest)│ │ (retrieval)│  │  │  │ LLM Provider         │ │
│  └─────────┘ └────────────┘  │  │  └──────────────────────┘ │
│  ┌─────────┐ ┌────────────┐  │  └───────────────────────────┘
│  │ChromaDB │ │ BM25 Index │  │
│  │ (vector)│ │  (lexical) │  │
│  └─────────┘ └────────────┘  │
└──────────────────────────────┘

Storage: SQLite (metadata) + Local files (PDFs, outputs)
```

**Key Components:**
- **Chunker**: Page-aware text splitting (900 chars, 150 overlap)
- **Embedder**: sentence-transformers for local embedding
- **ChromaDB**: Vector store for semantic search
- **BM25**: Lexical index for keyword matching
- **Agents**: Course/Paper/Slides generators with citation tracking
- **Task Queue**: Background processing with progress and retry

---

## Privacy & Local-First

StudyFlow AI is designed with privacy as a core principle:

- **All data stays local**: PDFs, chunks, indexes, and outputs are stored on your machine
- **No telemetry**: We don't collect any usage data
- **API keys in memory only**: Keys are never written to disk (only in session state)
- **Optional cloud LLM**: You choose whether to use cloud APIs or local models
- **Exportable data**: Bundle export includes all your data in portable format

**Your data locations:**
```
workspaces/<workspace-id>/
├── uploads/     # Your imported PDFs
├── index/       # Vector + BM25 indexes
├── outputs/     # Generated content
├── runs/        # Generation logs
└── coach/       # Coaching sessions
```

---

## Roadmap

Planned improvements (no timelines):

1. **Ollama integration**: Run with local LLMs (Llama 3, Mistral)
2. **Obsidian plugin**: Export to your knowledge base
3. **Anki export**: Generate flashcards from content
4. **Knowledge graph**: Visualize concept relationships
5. **Mobile-responsive UI**: Better experience on tablets

---

## Contributing

Contributions are welcome! Here's how to get started:

### Development Setup

```bash
# Clone and install dev dependencies
git clone https://github.com/li147852xu/studyflow-ai.git
cd studyflow-ai
pip install -e ".[dev]"

# Run linting
ruff check .

# Run tests
pytest -q

# Run the app locally
streamlit run app/main.py
```

### Code Quality

We use:
- **ruff** for linting and formatting
- **pytest** for testing
- **GitHub Actions** for CI

Before submitting a PR:
```bash
ruff check .
pytest -q
python -m compileall .
```

---

## License

This project is for educational and personal use.

---

<p align="center">
  <strong>StudyFlow AI v2.10.0</strong><br>
  Made with care for learners and researchers
</p>
