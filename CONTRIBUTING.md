# Contributing

Thanks for improving Enterprise RAG Engine. Changes should keep the system's
retrieval, generation, ingestion, and transport boundaries explicit.

## Development setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Normal tests must remain offline: inject or mock providers, model downloads,
clocks, filesystems, and stores where practical. Real-provider smoke tests must
stay explicit and opt-in.

## Pull requests

1. Explain the user-visible or operational requirement.
2. Describe affected contracts and persisted-data compatibility.
3. Add focused tests for behavior changes.
4. Run the focused tests, then the full offline suite.
5. Update documentation and evaluation evidence when retrieval, chunking,
   prompts, citations, or public behavior changes.
6. Check the complete diff for secrets, private documents, indexes, logs, and
   unrelated edits.

Read [AGENTS.md](AGENTS.md) for repository-wide engineering rules and
[rag_spec.md](rag_spec.md) for RAG behavior and data contracts.

## Commit style

Use a short imperative summary with an optional conventional prefix, for
example `feat: add readiness diagnostics` or `docs: publish evaluation scope`.

## Security

Do not open a public issue containing credentials, private enterprise content,
provider payloads, or sensitive logs. Follow [SECURITY.md](SECURITY.md).
