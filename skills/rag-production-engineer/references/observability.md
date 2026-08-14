# Observability and tracing

Use this reference to make each answer explainable from source ingestion through
retrieval and generation. Combine traces for diagnosis, metrics for trends,
logs for events, and evaluations for quality.

## Define the trace hierarchy

Create one root trace for a user request. Represent each material operation as a
child span with consistent names and attributes.

```text
rag.request
|-- policy.resolve
|-- query.classify
|-- query.rewrite
|-- retrieve.dense
|-- retrieve.lexical
|-- retrieve.fuse
|-- rerank
|-- context.assemble
|-- generate
|-- citation.validate
`-- response.finalize
```

For agentic RAG, add a span for planning and one span per tool call. For
ingestion, create a separate trace rooted at `ingest.document` with parse,
chunk, embed, and index spans.

## Capture useful attributes

Record identifiers and measurements required to reproduce behavior.

- request, session, trace, tenant, and anonymized user identifiers;
- query class, route, locale, and policy decision;
- provider, model, deployment, region, and configuration version;
- parser, chunker, embedding, index, prompt, and evaluation versions;
- filters and candidate, included, excluded, and cited document IDs;
- retrieval, fusion, and reranking scores where available;
- input, output, and cached token counts;
- stage latency, queue time, retry count, timeout, and status;
- estimated or billed cost and cache outcome;
- fallback name, reason, and degradation level.

Do not log raw prompts, documents, or personal data by default. Use redaction,
hashing, sampling, access controls, encryption, and retention limits based on
the data classification.

### Guide instrumentation changes

Start from the question an operator must answer, then locate the existing
telemetry boundary and propagation mechanism. Reuse current tracing, metrics,
and logging libraries. Add the smallest event or span that distinguishes the
relevant routes, decisions, and failure reasons without copying payloads.

Test emitted telemetry as an observable contract when the repository has a
test recorder or exporter. Also test the user-visible behavior because a span
can be correct while the fallback, authorization decision, or response is
wrong. Do not introduce a new observability vendor merely to add one signal.

### Preserve trace context and sampling coherence

Propagate the incoming trace context through retrieval, reranking, generation,
validation, fallback, and tool boundaries. Child spans keep the trace
identifier and receive distinct span identifiers. Across queues or fan-out,
use the host stack's context carrier and span links where a strict parent-child
relationship would be false. Test the exported trace graph, not only calls to
the instrumentation API.

Choose sampling from the operator question and cost budget. Head sampling can
use only information known when the trace starts; outcome-aware retention
requires a tail or buffered decision. Keep coherent traces for errors,
timeouts, denials, fallbacks, and selected evaluation cohorts. Do not derive
population rates from biased trace samples unless the sampling probability is
known and the calculation compensates for it.

### Keep telemetry safe and bounded

Separate diagnostic attributes from metric dimensions. Put bounded route,
status, operation, provider, model, and version values on metrics. Keep request,
tenant, user, document, and session identifiers out of metric dimensions. Use
protected traces or logs only when those identifiers are necessary and allowed
by the data policy.

Treat raw queries, retrieved content, prompts, tool arguments, and generated
answers as content capture, not normal metadata. Disable content capture by
default, redact before export, and test the serialized telemetry for secrets.
Hashing is not anonymization when the source space is small or reversible.

Treat semantic conventions as a versioned integration contract. Inspect the
installed SDK, emitted schema, and backend support before adopting names from a
newer convention. Keep the application's internal outcome vocabulary stable
when OpenTelemetry, a vendor SDK, or a GenAI convention changes.

## Define metrics and service indicators

Build service indicators around the user outcome and each dependency.

- successful grounded answer rate;
- retrieval recall from sampled labeled traffic;
- empty, low-confidence, and unauthorized retrieval rates;
- citation validation and abstention rates;
- p50, p95, and p99 latency by stage, route, and provider;
- error, timeout, retry, fallback, and circuit-open rates;
- cost per request and cost per successful grounded answer;
- token, candidate, and context-size distributions;
- ingestion freshness lag, queue age, and indexing failures.

Keep metric labels bounded. Put document IDs, full error text, and request IDs
in traces or logs, not metric dimensions.

### Guide SLO and alert implementation

Define a good event from the user's RAG outcome. Depending on the product, that
can require an authorized, grounded, non-abstained answer within a latency and
freshness budget, not merely an HTTP success. Keep availability, grounded
quality, latency, freshness, and cost as separate indicators when they have
different owners or mitigations.

Compute burn against an explicit SLO error budget using counters and latency
histograms. Require paired short and long windows for fast-burn paging so a
brief spike does not page while a sustained incident is missed. Define bounded
behavior for no-traffic and low-volume windows. Every firing alert needs a
machine-readable reason, owner, severity, diagnostic path, and tested runbook.
Do not create a dashboard or paging platform when the repository only needs a
local instrumentation or alert-rule correction.

## Build operational views

Create a small set of dashboards with clear owners and actions.

- An outcome view shows quality, grounded success, abstention, latency, and
  cost.
- A retrieval view shows empty results, recall samples, score distributions,
  filters, duplicates, and reranker behavior.
- A provider view compares latency, errors, rate limits, spend, and fallbacks.
- An ingestion view shows freshness, throughput, failures, queue age, and index
  reconciliation.
- A release view compares prompt, model, embedding, and index versions.

Link dashboard points to representative traces. A graph without a path to raw
evidence is weak for debugging.

## Alert on actionable symptoms

Alert when a responder has a defined action. Use sustained windows and burn-rate
alerts to reduce noise.

Examples include service-level objective burn, freshness breaches, permission
violations, fallback spikes, provider errors, p99 latency changes, cost surges,
queue age, and evaluation regressions.

Document the owner, severity, diagnostic query, immediate mitigation, and
escalation path. Test alerts and runbooks during failure injection.

## Use the trace analyzer

Export one JSON object per line with at least `name` and `duration_ms`. Optional
fields include `status`, `provider`, `model`, `cost_usd`, `fallback`, and
`timestamp`.

Run the analyzer with:

```bash
python3 scripts/analyze_traces.py traces.jsonl
```

The output summarizes latency percentiles, errors, cost, and fallbacks overall
and by span name. Use a full observability backend for high-cardinality search,
retention, sampling, and distributed context propagation.
