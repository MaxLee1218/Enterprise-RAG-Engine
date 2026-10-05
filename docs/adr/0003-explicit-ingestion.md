# ADR-0003: Keep ingestion explicit and offline

- Status: Accepted
- Context: Embedding, chunking, and persisted metadata changes can invalidate
  indexes. Rebuilding during a user query would make latency and data mutation
  unpredictable.
- Decision: Only the ingestion workflow writes document indexes. Query paths
  fail with an actionable readiness error when the configured index is absent.
- Consequences: Operations must run ingestion deliberately before serving RAG
  queries. This makes writes auditable and prevents hidden rebuilds, but the
  current project still needs stronger stale-chunk reconciliation and migration
  tooling.
