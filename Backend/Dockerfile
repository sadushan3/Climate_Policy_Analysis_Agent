# ---------- stage 1: model cache ----------
# Downloading the embedding + reranker weights is the slowest part of a build and
# it never changes between code edits, so it gets its own cached layer.
FROM python:3.11-slim AS models

ENV HF_HOME=/opt/hf \
    TRANSFORMERS_NO_TF=1 \
    USE_TF=0

RUN pip install --no-cache-dir "sentence-transformers==3.3.1" "torch==2.5.1" \
      --extra-index-url https://download.pytorch.org/whl/cpu

RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# ---------- stage 2: runtime ----------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf \
    TRANSFORMERS_OFFLINE=1 \
    TRANSFORMERS_NO_TF=1 \
    USE_TF=0 \
    DATA_DIR=/data

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
      --extra-index-url https://download.pytorch.org/whl/cpu

COPY --from=models /opt/hf /opt/hf
COPY app ./app
COPY eval ./eval

# Never run as root.
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /data && chown -R appuser:appuser /data /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
