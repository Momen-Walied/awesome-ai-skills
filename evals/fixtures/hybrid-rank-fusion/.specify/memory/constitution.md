# Hybrid retrieval constitution

- Apply tenant authorization before every retrieval and fusion path.
- Combine rankings without assuming dense and lexical scores are comparable.
- Deduplicate by stable document identifier before applying the final limit.
- Keep the dense-only route available as rollback.
- Record bounded route and candidate-count telemetry without query or content.
- Implement `specs/001-hybrid-rank-fusion/spec.md`.
