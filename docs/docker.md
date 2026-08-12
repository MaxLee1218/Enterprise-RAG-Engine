# Docker Runtime

The formal image packages the Enterprise RAG HTTP service and its explicit
ingestion command. It does not contain credentials, source documents, a Chroma
index, or locally downloaded models.

## Runtime contract

| Concern | Contract |
|---|---|
| Python | CPython 3.11 on `python:3.11-slim` |
| Dependency installation | Pinned direct production dependencies from `requirements-runtime.txt`; this repository is not an installable Python package |
| Default server | `uvicorn app.api:app --host 0.0.0.0 --port 8000` |
| Runtime identity | non-root UID/GID `10001:10001` |
| Health | `GET /health`; process health only, not index/model/provider readiness |
| Ask | `POST /ask` with `{"question": "..."}` |
| Ingestion | `python scripts/ingest.py ...`; always an explicit offline operation |
| Persistent data | `/app/data` |
| Read-only documents | `/app/enterprise-documents` |

The runtime image contains only `app/` and the ingestion, ask, and query CLI
scripts. Development, evaluation, report-generation, test, and document-build
dependencies remain in `requirements.txt` and are intentionally excluded from
the service image. The builder installs PyTorch from its official CPU wheel
index so a CPU service image does not acquire CUDA runtime packages.

## Data model

```text
enterprise-rag-engine:local
  application + pinned runtime dependencies
              |
              +-- reads /app/enterprise-documents (read-only bind mount)
              +-- reads/writes /app/data (named volume)
                    +-- supplier_quality/chroma  generated vector index
                    +-- parents/parents.sqlite3  optional parent-child store
                    +-- faq.db                   optional FAQ store
                    +-- model-cache              downloaded model cache
```

The query service never ingests documents during startup. Chroma uses SQLite
and local index files, so `/app/data` must remain writable by UID 10001 even for
query containers. Source documents should be mounted read-only and are not
required after a standard-mode index has been built.

The embedding and optional Cross-Encoder models are downloaded on first use.
`HF_HOME` and `SENTENCE_TRANSFORMERS_HOME` point under
`/app/data/model-cache`, so a named data volume prevents repeated downloads
across ingestion and query containers. The locally present development model
is roughly 477 MB and is excluded from the image.

## Build

From the repository root:

```bash
docker build -t enterprise-rag-engine:local .
```

Inspect the immutable runtime metadata:

```bash
docker image inspect enterprise-rag-engine:local
docker history --no-trunc enterprise-rag-engine:local
docker run --rm enterprise-rag-engine:local id
```

The final command must report UID 10001, not root. The image history must not
contain a credential. Never pass a secret as a Docker build argument.

## Create the persistent volume

```bash
docker volume create enterprise-rag-data
```

The examples below use this volume for the Chroma index and model cache.

## Ingest Supplier Quality documents

The repository contains five synthetic controlled Supplier Quality PDFs. Mount
the corpus read-only and run ingestion as a one-shot container:

```bash
docker run --rm \
  -v enterprise-rag-data:/app/data \
  -v "$PWD/enterprise-documents:/app/enterprise-documents:ro" \
  enterprise-rag-engine:local \
  python scripts/ingest.py \
    --input /app/enterprise-documents/pdf \
    --extensions .pdf \
    --persist-path /app/data/supplier_quality/chroma \
    --collection supplier_quality_demo
```

Use `--reset` only for an intentional rebuild of the named collection. The
command does not modify the mounted PDFs. Without `--reset`, stable chunk IDs
are upserted; source-level deletion of stale chunks is not implemented.

First ingestion requires network access if the embedding model is not already
in the volume cache. A model download failure leaves no successful ingestion
summary and the command exits non-zero.

## Run the HTTP service

Inject the DeepSeek credential at runtime. `--env-file` does not add it to the
image or its history:

```bash
docker run -d \
  --name enterprise-rag-engine \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  -v enterprise-rag-data:/app/data \
  enterprise-rag-engine:local
```

Uvicorn access and application logs go to container stdout/stderr. The current
bounded request audit also writes `/app/logs/rag_requests.jsonl` inside the
container; it is not part of the knowledge volume and write failures do not
fail requests.

The default command contains no development reload process. Docker sends
SIGTERM on `docker stop`, which Uvicorn handles with graceful server shutdown.

## Health

```bash
curl --fail http://127.0.0.1:8000/health
docker inspect --format '{{json .State.Health}}' enterprise-rag-engine
```

The existing health contract reports that the API process is serving requests.
It intentionally does not load the embedding model, open the index, or call
DeepSeek. An empty volume can therefore be healthy while `/ask` returns the
existing explicit `503 Vector store is not ready` response.

## Ask

```bash
curl --fail-with-body \
  -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -H 'X-Trace-ID: docker-supplier-quality-001' \
  -d '{"question":"How is supplier defect rate calculated?"}'
```

The response contract is unchanged:

```json
{
  "answer": "...",
  "sources": [],
  "contexts": [],
  "route": "rag",
  "latency_ms": 0,
  "rag_trace_id": "docker-supplier-quality-001"
}
```

Successful grounded answers should contain non-empty `sources` and `contexts`.
Source and context metadata retain the current document and chunk provenance.
The whole-document PDF loader does not currently expose page numbers as chunk
metadata.

## Persistence check

Remove and recreate only the container, then reuse the same volume:

```bash
docker stop enterprise-rag-engine
docker rm enterprise-rag-engine

docker run -d \
  --name enterprise-rag-engine \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  -v enterprise-rag-data:/app/data \
  enterprise-rag-engine:local
```

After the healthcheck passes, repeat the `/ask` request. The second container
uses the same knowledge index and model cache.

## Reset

Deleting the named volume permanently removes the generated index, FAQ/parent
stores, and downloaded model cache. Stop containers using it first:

```bash
docker rm -f enterprise-rag-engine
docker volume rm enterprise-rag-data
```

Create a new volume and repeat ingestion to rebuild from source documents. Do
not delete or rewrite a production knowledge volume as an incidental query
operation.

## Copilot integration

The sibling `Agentic-Enterprise-Knowledge-Copilot` Compose topology already
uses the image and paths defined here:

```env
ENTERPRISE_RAG_IMAGE=enterprise-rag-engine:local
ENTERPRISE_RAG_DEEPSEEK_API_KEY=...
```

Its internal URL is:

```text
RAG_BASE_URL=http://enterprise-rag-engine:8000
```

Run that project's `enterprise-rag-ingest` profile once for a fresh named
volume, then start the normal topology. The Copilot communicates only through
`GET /health` and `POST /ask`; it does not mount or read Chroma directly.

## Resource observation

Model memory and disk use dominate this service. Inspect the actual target
machine rather than treating local observations as capacity guarantees:

```bash
docker image inspect enterprise-rag-engine:local --format '{{.Size}}'
docker run --rm -v enterprise-rag-data:/app/data \
  enterprise-rag-engine:local du -sh /app/data
docker stats --no-stream enterprise-rag-engine
```

One Apple Silicon Docker Desktop validation of this image observed a roughly
490 MB arm64 image, 74 MiB for the lazy process-health state, about 1.0 GiB
after loading embedding and reranker models, a 2.7 MB 81-chunk Chroma index,
and a 476 MB persistent model cache. Fresh ingestion of the five PDFs took
about 40 seconds with the model download available. These are local
observations, not production capacity commitments.

Startup process health is lightweight because the pipeline is lazy. The first
real `/ask` loads the embedding model, the full stored corpus for BM25, and—if
enabled—the reranker, so its latency and peak RAM are higher than `/health`.

## Troubleshooting

### Index missing

`/health` may be 200 while `/ask` returns 503. Run the explicit ingestion
container against the same `/app/data` volume and collection.

### Permission denied or volume permission error

The service runs as UID/GID 10001. A Docker named volume initialized by this
image has the correct ownership. For a bind-mounted data directory, make the
specific directory writable by 10001; do not use recursive mode 777.

### Model download failure

Check outbound HTTPS/DNS access, available disk space, and permissions under
`/app/data/model-cache`. Reusing the named volume avoids downloading on every
container recreation.

### Health remains unhealthy

Inspect `docker logs enterprise-rag-engine` and the health state. Confirm port
8000 is free, the command was not overridden, and the process can write its
runtime directories.

### `/ask` returns 500

Confirm `DEEPSEEK_API_KEY`, base URL, model, and provider access. API errors are
translated to safe responses; inspect container logs for the error category.

### No sources

Confirm the requested collection was ingested and that `VECTOR_DB_PATH` and
`VECTOR_COLLECTION_NAME` match between ingestion and the server. Do not use a
fixture result as a real retrieval gate.

### Port conflict

Change only the host side, for example `-p 127.0.0.1:8011:8000`. The service and
Copilot network contract remain port 8000 inside the container.

### Out of memory

Disable only optional components through existing configuration when that is
acceptable for the target topology, or allocate more memory. Do not change the
embedding model for an existing index without a controlled compatibility
rebuild.
