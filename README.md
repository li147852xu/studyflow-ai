# StudyFlow v3

**A local-first Course & Research Operating System with coverage-audited RAG for comprehensive academic workflows.**

---

## Quick Start

### Docker (Recommended)

```bash
# 1) Clone
git clone https://github.com/li147852xu/studyflow-ai.git
cd studyflow-ai

# 2) Set your LLM environment
export STUDYFLOW_LLM_BASE_URL=https://api.openai.com/v1
export STUDYFLOW_LLM_API_KEY=sk-your-key
export STUDYFLOW_LLM_MODEL=gpt-4o-mini

# 3) Start
docker compose up --build

# 4) Open
# UI: http://localhost:8501
# API: http://localhost:8000 (optional)
```

### Local Install

```bash
pip install -e .
streamlit run app/main.py
```

---

## Core Features

### Course Management
- **Course Info**: name, code, instructor, semester, weekly schedule
- **Lectures**: organize materials by lecture/date/topic
- **Materials**: slides, notes, readings linked to lectures
- **Assignments**: specs, analysis, due dates, status tracking
- **Exam Tools**: generate exam blueprints with coverage reports

### Research Platform
- **Projects**: goals, scope, milestones
- **Papers**: import, parse, generate paper cards (summary, contributions, pros/cons)
- **Ideas**: AI-generated novelty points with multi-turn confirmation dialogue
- **Experiments**: plans from confirmed ideas, run logs, progress tracking
- **Decks**: presentation generation with citations and coverage

### Timetable & Todos
- Course schedules auto-populate dashboard
- Custom events and tasks
- Global todo list linked to courses/projects

### AI Assistant
- Scoped queries (per course or project)
- Global queries with map-reduce coverage
- Coverage reports showing which docs/lectures were included

---

## RAG Coverage System (v3 Core)

StudyFlow v3 solves the "full course/project coverage" problem:

1. **Index Assets**: Each document gets offline-generated summary (300-800 tokens), outline, and key entities
2. **Query Classifier**: Detects local vs global queries
3. **Map-Reduce**: For global queries, maps over all docs then reduces with coverage audit
4. **Coverage Report**: Shows included docs, missing docs, per-lecture evidence counts
5. **Token Budget**: Configurable limits (default: map ≤250 tokens/doc, reduce ≤600 tokens)

When coverage is incomplete, UI shows actionable buttons: "Rebuild Index", "Expand Scope", "Import Missing".

---

## UI Structure

| Screen | Purpose |
|--------|---------|
| **Dashboard** | Today's schedule, todos, recent activity, quick stats |
| **Library** | Document repository (link to courses/projects) |
| **Courses** | Course management with lectures, assignments, exams |
| **Research** | Projects, papers, ideas, experiments, decks |
| **AI Assistant** | Scoped Q&A with coverage reports |
| **Tools** | Tasks, diagnostics, activity history, exports, help |
| **Settings** | LLM config, retrieval mode, theme, language |

---

## Configuration

### Environment Variables

```bash
# Required for generation
STUDYFLOW_LLM_BASE_URL=https://api.openai.com/v1
STUDYFLOW_LLM_API_KEY=sk-your-key
STUDYFLOW_LLM_MODEL=gpt-4o-mini

# Optional
STUDYFLOW_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
STUDYFLOW_OCR_MODE=off    # off | auto | on
STUDYFLOW_WORKSPACES_DIR=./workspaces
```

### Retrieval Modes

| Mode | Description |
|------|-------------|
| **Vector** | Semantic search via embeddings |
| **BM25** | Keyword-based lexical search |
| **Hybrid** | Fused Vector + BM25 (best accuracy) |

---

## CLI Reference

```bash
# System health
studyflow doctor
studyflow doctor --deep

# Workspace
studyflow workspace create "My Project"
studyflow workspace list

# Documents
studyflow ingest --workspace <id> document.pdf

# Index
studyflow index build --workspace <id>
studyflow index status --workspace <id>

# Query
studyflow query --workspace <id> --mode hybrid "your question"

# Migration (v2 → v3)
studyflow migrate
```

---

## Verification

```bash
python scripts/verify_v3_release.py
python -m compileall .
pytest -q
ruff check .
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "LLM not configured" | Settings → enter Base URL, Model, API Key |
| Generation disabled | Check dashboard setup status |
| Coverage incomplete | Use "Rebuild Index" or "Import Missing" buttons |
| Task failed | Tools → Tasks → Retry button |

### Diagnostic Tools
- **Doctor**: Tools → Diagnostics → Doctor
- **Index Rebuild**: Tools → Diagnostics → Rebuild Index
- **Task Center**: Tools → Tasks (view/retry/cancel)

---

## Privacy & Local-First

- All data stays on your machine
- No telemetry or usage tracking
- API keys stored in session only
- Exportable data bundles

```
workspaces/<workspace-id>/
├── uploads/     # Imported documents
├── index/       # Vector + BM25 indexes
├── outputs/     # Generated content
└── vault/       # Versioned assets
```

---

## Development

```bash
git clone https://github.com/li147852xu/studyflow-ai.git
cd studyflow-ai
pip install -e ".[dev]"

# Lint
ruff check .

# Test
pytest -q

# Run
streamlit run app/main.py
```

---

## License

This project is for educational and personal use.

---

<p align="center">
  <strong>StudyFlow v3.0.0</strong><br>
  Local-first Course & Research OS
</p>
