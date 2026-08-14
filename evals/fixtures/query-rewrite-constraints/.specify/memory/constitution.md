# Query transformation constitution

- Keep authorization and retrieval constraints outside generated query text.
- Preserve the original query as a bounded retrieval path.
- Reject rewrites that lose immutable literals required by the request.
- Bound and deduplicate rewrites before issuing retrieval calls.
- Deduplicate evidence by stable document identifier across query paths.
- Record bounded transformation decisions without query or document content.
- Implement `specs/001-query-rewrite-constraints/spec.md`.
