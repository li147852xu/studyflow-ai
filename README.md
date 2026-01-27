# StudyFlow AI

<p align="center">
  <strong>Your AI-Powered Study Companion</strong><br>
  A local-first study workspace for PDFs with intelligent coaching, knowledge extraction, and presentation generation.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#documentation">Documentation</a>
</p>

---

## Overview

StudyFlow AI transforms how you study and research. Import PDFs, get intelligent summaries, generate study materials, and receive personalized coaching - all while keeping your data local and private.

**Key Benefits:**
- 🔒 **Privacy-First**: All data stays on your machine
- 🤖 **AI-Powered**: Leverages LLMs for intelligent content generation
- 📚 **Multi-Format**: Courses, papers, presentations in one workspace
- 🎯 **Personalized**: Adaptive coaching based on your learning needs

## Features

### 📖 Document Management
- **Multi-source Import**: Upload PDFs, import from Zotero, arXiv, DOI, or URL
- **Smart Categorization**: Organize by type (Course/Paper/Other) with course grouping
- **Auto-Summaries**: LLM-generated one-line descriptions for quick reference
- **OCR Support**: Extract text from scanned documents (auto/on/off modes)

### 🎓 Course Learning
- **Course Overview**: Generate comprehensive course summaries
- **Cheat Sheets**: Create quick-reference review materials
- **Knowledge Q&A**: Ask questions and get answers from course materials
- **Explain Selection**: Get explanations in multiple modes (concept, proof, example, summary)

### 📄 Research Papers
- **Paper Cards**: Structured analysis with contributions, strengths, weaknesses
- **Multi-Paper Comparison**: Compare papers around research questions
- **Citation Management**: Track and export citations

### 🎬 Presentations
- **Auto-Generation**: Create Marp-format slide decks from any document
- **Flexible Duration**: 1-30 minute presentations
- **Q&A Lists**: Auto-generated discussion questions

### 🧑‍🏫 Study Coach
- **Two-Phase Guidance**: Framework → Review feedback approach
- **Session Management**: Named sessions with full history
- **Smart References**: Automatically references your entire library

### ⚡ Advanced Features
- **Hybrid Retrieval**: Vector + BM25 search modes
- **Asset Versioning**: Pin, rollback, and diff generated outputs
- **Background Tasks**: Queue-based processing with progress tracking
- **Plugin System**: Extensible importers and exporters

## Quick Start

### Prerequisites
- Python 3.10+
- An OpenAI-compatible API key

### Installation

```bash
# Clone the repository
git clone https://github.com/li147852xu/studyflow-ai.git
cd studyflow-ai

# Install dependencies
pip install -e .

# Configure your API key
cp .env.example .env
# Edit .env and add your LLM API key
```

### Launch

```bash
streamlit run app/main.py
```

Open your browser to `http://localhost:8501`

## Usage

### Basic Workflow

1. **Create a Project**: Select or create a workspace in the sidebar
2. **Import Documents**: Upload PDFs or import from external sources
3. **Build Index**: The system automatically indexes your documents
4. **Generate Content**: Use the Create page to generate materials
5. **Get Coaching**: Use the Study Coach for personalized guidance

### Navigation

| Page | Purpose |
|------|---------|
| **Start** | Quick overview and one-click workflows |
| **Library** | Import, organize, and filter documents |
| **Create** | Generate courses, papers, and presentations |
| **Tools** | Coach, tasks, settings, and diagnostics |
| **Help** | Documentation and troubleshooting |

### CLI Commands

```bash
# System health check
studyflow doctor

# Workspace management
studyflow workspace create <name>

# Document ingestion
studyflow ingest --workspace <id> --ocr auto <pdf_path>

# Query your documents
studyflow query --workspace <id> --mode hybrid "your question"

# Generate content
studyflow gen --workspace <id> --type slides --source <doc_id>

# Study coaching
studyflow coach start --workspace <id> --problem "..."
```

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```env
STUDYFLOW_LLM_BASE_URL=https://api.openai.com/v1
STUDYFLOW_LLM_MODEL=gpt-4
STUDYFLOW_LLM_API_KEY=your-api-key
STUDYFLOW_EMBED_MODEL=text-embedding-3-small
```

### Config Profiles

For advanced configuration, create `config.toml` from `config.example.toml`:

```toml
[profiles.default]
llm_base_url = "https://api.openai.com/v1"
llm_model = "gpt-4"
embed_model = "text-embedding-3-small"
api_key_env = "OPENAI_API_KEY"
```

## API Mode (Optional)

Run StudyFlow as a backend service:

```bash
# Start the server
studyflow api serve --host 127.0.0.1 --port 8000

# In the UI: Settings → API Mode → Set Base URL
```

## Documentation

### In-App Help
The application includes comprehensive help accessible via the Help page, covering:
- Getting started guide
- Feature walkthroughs
- Troubleshooting tips

### Data Storage
All data is stored locally:
```
workspaces/<workspace-id>/
├── uploads/     # Imported PDFs
├── index/       # Vector + BM25 indexes
├── outputs/     # Generated content
├── runs/        # Generation logs
└── coach/       # Coaching sessions
```

### OCR Setup (Optional)

For scanned PDFs:

```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

# Windows
choco install tesseract
```

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python, SQLite
- **AI/ML**: OpenAI API, sentence-transformers
- **Search**: ChromaDB (vector), rank_bm25 (lexical)
- **OCR**: Tesseract (optional)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is for educational and personal use.

## Disclaimer

- You must provide your own API key
- API keys are never stored on disk
- All data remains local unless you configure external services

---

<p align="center">
  Made with ❤️ for learners and researchers
</p>
