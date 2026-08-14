# Grounded answer SLO burn alert

## User scenario

The RAG API returns HTTP 200 for ungrounded and slow answers, so transport
success alone hides user-visible failures and produces misleading alerts.

## Acceptance scenarios

1. An HTTP-successful but ungrounded answer counts as a bad event.
2. An HTTP-successful grounded answer outside the latency budget counts as bad.
3. Fast-burn paging requires both the short and long windows to exceed their
   configured burn thresholds.
4. A sustained fast burn fires with a machine-readable reason, owner, and
   runbook.
5. A window with no requests produces zero burn and does not alert.
