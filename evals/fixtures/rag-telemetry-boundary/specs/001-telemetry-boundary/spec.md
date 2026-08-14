# RAG telemetry boundary

## User scenario

Operators need to correlate a RAG request without leaking payloads or creating
one metric series per tenant, request, or document.

## Acceptance scenarios

1. A sampled healthy request exports root, retrieval, and generation spans under
   one incoming trace identifier.
2. Exported telemetry contains no raw query, document content, answer, tenant
   identifier, or request identifier.
3. Request metrics use only the bounded `route` and `status` dimensions.
4. A non-head-sampled fallback still exports the complete degraded trace.
5. Healthy and fallback user-visible responses remain unchanged.
