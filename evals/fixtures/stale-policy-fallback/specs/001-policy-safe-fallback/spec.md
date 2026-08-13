# Policy-safe retrieval fallback

## User scenario

When the primary retriever times out, the service may use the fallback index
only if its authorization policy sequence meets the request requirement.

## Acceptance scenarios

1. A healthy primary retriever remains the selected route.
2. A fresh fallback serves only authorized tenant results and records why it
   was selected.
3. A fallback with stale policy state returns no results and records a blocked
   fallback with the stale-policy reason.
4. Cross-tenant chunks never appear on the fallback route.
