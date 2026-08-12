FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv

RUN python -m venv "${VIRTUAL_ENV}"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY requirements-runtime.txt /tmp/requirements-runtime.txt
RUN pip install --upgrade pip && \
    pip install --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 && \
    pip install --requirement /tmp/requirements-runtime.txt


FROM python:3.11-slim AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MINI_RAG_SKIP_DOTENV=1 \
    VECTOR_DB_PATH=/app/data/supplier_quality/chroma \
    RAG_PARENT_STORE_PATH=/app/data/parents/parents.sqlite3 \
    FAQ_DB_PATH=/app/data/faq.db \
    HF_HOME=/app/data/model-cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/data/model-cache/sentence-transformers

RUN groupadd --gid "${APP_GID}" rag && \
    useradd --uid "${APP_UID}" --gid rag --create-home \
        --home-dir /home/rag --shell /usr/sbin/nologin rag && \
    mkdir -p \
        /app/data/model-cache/huggingface \
        /app/data/model-cache/sentence-transformers \
        /app/data/parents \
        /app/data/supplier_quality/chroma \
        /app/enterprise-documents \
        /app/logs && \
    chown -R rag:rag /app /home/rag

WORKDIR /app

COPY --from=builder --chown=rag:rag /opt/venv /opt/venv
COPY --chown=rag:rag app /app/app
COPY --chown=rag:rag scripts/ingest.py /app/scripts/ingest.py
COPY --chown=rag:rag scripts/ask.py /app/scripts/ask.py
COPY --chown=rag:rag scripts/query.py /app/scripts/query.py

USER 10001:10001

EXPOSE 8000
VOLUME ["/app/data"]

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=12 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
