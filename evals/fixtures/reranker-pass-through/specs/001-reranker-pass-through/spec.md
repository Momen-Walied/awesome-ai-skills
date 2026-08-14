# Reranker pass-through fallback

## User scenario

The reranker improves the first two authorized candidates, but the service drops
the untouched retrieval tail. On timeout or malformed IDs, it returns partial or
empty evidence instead of the known retrieval ranking.

## Acceptance scenarios

1. Successful reranking reorders only the configured head window and appends the
   untouched tail in original order.
2. Timeout returns the complete original ranking and records `timeout`.
3. Unknown, missing, or duplicate reranker IDs make the output malformed and
   return the complete original ranking.
4. Empty retrieval or a zero-sized rerank window skips the reranker and
   preserves the original ranking.
5. Authorization remains enforced before reranking.
6. Disabling reranking preserves the original retrieval route.
7. Telemetry records route, reason, and bounded counts without query, document
   content, or raw scores.
