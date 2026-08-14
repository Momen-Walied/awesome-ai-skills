# RAG telemetry constitution

- Preserve one trace context across the complete request path.
- Keep raw query, document, answer, tenant, and request values out of telemetry.
- Use bounded metric dimensions and keep diagnostic identifiers in protected traces.
- Retain complete degraded traces even when healthy traffic is sampled.
- Preserve user-visible behavior while correcting instrumentation.
- Implement `specs/001-telemetry-boundary/spec.md`.
