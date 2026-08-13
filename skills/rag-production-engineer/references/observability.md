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
