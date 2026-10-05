# GitHub Repository Presentation

Use these values in the repository settings after the corresponding files are
merged into the default branch.

## About

**Description**

> Test-backed enterprise RAG engine with hybrid retrieval, reranking, grounded sources, abstention, FastAPI, Docker, and offline evaluation.

**Topics**

```text
rag
retrieval-augmented-generation
fastapi
chromadb
hybrid-search
bm25
sentence-transformers
reranking
llm
rag-evaluation
python
enterprise-ai
```

**Social preview**

Upload [`docs/assets/social-preview.png`](assets/social-preview.png). The source
is generated together with the README animation by
`scripts/generate_readme_demo.py`.

## Recommended repository settings

- Enable GitHub Actions and require the `Python 3.11 · offline test suite`
  check before merging into `main`.
- Enable private vulnerability reporting.
- Enable Dependabot security updates.
- Keep the checked-in Apache-2.0 license visible in repository metadata.
- Pin the repository on the owner's public profile.

## First release

After CI succeeds on the intended release commit:

1. Confirm the Apache-2.0 license and public documentation.
2. Tag the verified revision as `v0.1.0`.
3. Use the `0.1.0` section in `CHANGELOG.md` as the release scope.
4. Do not claim production deployment, production SLOs, or provider-independent
   benchmark results in the release notes.
