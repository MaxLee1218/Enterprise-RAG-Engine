# ADR-0002: Combine dense and lexical retrieval

- Status: Accepted
- Context: Enterprise questions require semantic matching, while policy names,
  part numbers, thresholds, and abbreviations benefit from exact-term search.
- Decision: Retrieve candidates through Sentence Transformer embeddings and
  BM25, normalize scores per route, fuse them deterministically, and optionally
  rerank the candidate set with a Cross-Encoder.
- Consequences: Recall can benefit from complementary signals and component
  scores remain inspectable. BM25 is currently rebuilt in memory, fusion
  weights are fixed, and min-max normalized scores are not calibrated
  probabilities.
