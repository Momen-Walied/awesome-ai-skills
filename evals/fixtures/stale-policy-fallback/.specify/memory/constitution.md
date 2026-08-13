# Retrieval fallback constitution

- Resolve tenant authorization before returning candidates from any route.
- Serve fallback results only when fallback policy state is current enough.
- Preserve the primary route when it is healthy.
- Trace fallback selection or rejection without recording query text.
- Implement the scenarios in `specs/001-policy-safe-fallback/spec.md`.
