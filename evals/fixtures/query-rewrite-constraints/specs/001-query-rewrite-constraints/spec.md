# Constraint-preserving query transformation

## User scenario

The query rewriter improves semantic phrasing but can drop an exact product
identifier. The current service searches only generated rewrites, so a malformed
or timed-out rewrite can remove the only safe retrieval path.

## Acceptance scenarios

1. Enabling rewrites always searches the original query first.
2. A valid rewrite that preserves every immutable literal adds one retrieval
   path under the same tenant, locale, version, and exclusion constraints.
3. A rewrite that drops an immutable literal is not sent to retrieval.
4. Duplicate rewrites are removed and unique rewrites are capped before calls.
   A zero rewrite limit keeps the original-only route.
5. Rewriter timeout falls back to the original query and records a bounded
   machine-readable reason.
6. Documents returned by multiple query paths appear once by stable identifier.
7. Disabling rewrites preserves the original-only rollback route.
8. Telemetry contains route, reason, and counts without query or document text.
