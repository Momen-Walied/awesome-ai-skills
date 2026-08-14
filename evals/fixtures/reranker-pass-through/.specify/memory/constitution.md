# Reranker constitution

- Rerank only the configured head window after authorized retrieval.
- Treat reranker output as one valid permutation of the input window.
- Preserve the untouched retrieval tail in original order.
- Pass through the complete original ranking on timeout or malformed output.
- Keep reranking optional behind the existing rollback flag.
- Record bounded route and fallback metadata without query or content.
- Implement `specs/001-reranker-pass-through/spec.md`.
