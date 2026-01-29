# StudyFlow AI - Production Dockerfile
# Single-stage build for simplicity and reliability

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# Note: libgl1 replaces deprecated libgl1-mesa-glx in newer Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy dependency file first (for better caching)
COPY pyproject.toml README.md ./

# Copy source code
COPY app/ ./app/
COPY cli/ ./cli/
COPY core/ ./core/
COPY backend/ ./backend/
COPY service/ ./service/
COPY infra/ ./infra/
COPY scripts/ ./scripts/
COPY examples/ ./examples/

# Install the package
RUN pip install --no-cache-dir -e .

# Create data directory for persistent storage
RUN mkdir -p /data/workspaces

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TOKENIZERS_PARALLELISM=false
ENV STUDYFLOW_WORKSPACES_DIR=/data/workspaces
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose ports
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command: run Streamlit UI
CMD ["streamlit", "run", "app/main.py"]
