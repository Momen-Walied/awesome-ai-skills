# Architecture and decision model

Use this reference to turn product requirements into a RAG architecture without
adding components prematurely. Treat the architecture as a set of measurable
contracts rather than a vendor diagram.

## Frame the workload

Create a workload profile before selecting an architecture. Use ranges when
exact production numbers are unavailable, and label estimates clearly.

Capture these dimensions:

- corpus bytes, document count, chunk count, and vector dimensions;
- daily change volume, deletion rate, and freshness objective;
- queries per second, peak-to-average ratio, and concurrent requests;
- query classes, languages, modalities, and expected answer length;
- tenant count, tenant size skew, and authorization model;
- target p50, p95, and p99 latency and availability;
- quality thresholds by risk class;
- cost per successful answer and monthly budget;
- recovery point and recovery time objectives;
- operational capacity and deployment constraints.

Do not label a system "big data" from corpus size alone. A moderate corpus with
high update velocity, strict freshness, or heavy tenant skew can require more
engineering than a larger static corpus.

## Separate the planes

Reason about the system as independent planes with explicit contracts.

- The data plane parses, normalizes, identifies, chunks, enriches, embeds, and
  indexes content.
- The query plane classifies, rewrites, retrieves, reranks, assembles context,
  generates, cites, and validates answers.
- The control plane manages configuration, versions, rollout, access policy,
  quotas, and lifecycle operations.
- The evaluation plane manages datasets, experiments, regression gates, and
  production feedback.
- The observability plane connects traces, metrics, logs, costs, and source
  versions across the other planes.

Scale a plane independently only when measurements show a distinct bottleneck
or isolation requirement.

## Choose the minimum architecture

Use the first pattern that meets the acceptance thresholds.

| Pattern | Add when | Do not add merely because |
| --- | --- | --- |
| Direct lookup | Knowledge is small and deterministic | A vector store is available |
| Dense RAG | Queries are primarily semantic | It is the common tutorial pattern |
| Filtered RAG | Access, tenant, time, or type filters matter | Metadata exists |
| Hybrid RAG | Exact terms and identifiers lose recall | Lexical search sounds safer |
| Reranked RAG | Candidate recall is good but top ranks are weak | A reranker API is available |
| Multi-query | One phrasing misses distinct relevant evidence | More queries might improve recall |
| Hierarchical RAG | Fine chunks need larger parent context | Documents are simply long |
| Graph-assisted RAG | Explicit multi-hop relations drive answers | Entities can be extracted |
| Agentic RAG | Runtime tool and strategy choice is necessary | The application already uses agents |
| Distributed RAG | One plane needs independent scale or isolation | The corpus is called large |

## Budget the request path

Allocate the end-to-end latency objective across stages, then load-test the
slow path. Keep headroom for network variance and retries.

An initial budget can contain:

- authentication and policy resolution;
- query classification and rewriting;
- one or more retrieval calls;
- reranking;
- context assembly and compression;
- model time to first token and generation;
- citation validation and post-processing.

Do not spend the full service-level objective in the happy path. A practical
budget reserves capacity for queueing, one bounded retry, and traffic bursts.

## Define upgrade triggers

Attach each optional component to a measurable trigger and a rollback plan.

Examples include:

- add hybrid retrieval when exact-match query recall is below target;
- add reranking when recall at 20 passes but precision at 5 fails;
- add a cache when repeated requests are material and freshness semantics are
  defined;
- partition an index when tenant skew, memory, or tail latency crosses a tested
  threshold;
- add asynchronous fan-out when independent retrieval sources dominate latency;
- add agentic planning when static routing cannot cover validated query classes.

## Use the plan contract

Represent a design with the following top-level JSON fields so
`scripts/validate_rag_plan.py` can detect missing production concerns.

```json
{
  "use_case": {},
  "workload": {},
  "architecture": {},
  "ingestion": {},
  "retrieval": {},
  "generation": {},
  "evaluation": {},
  "observability": {},
  "reliability": {},
  "security": {},
  "vendors": {},
  "rollout": {}
}
```

Each object must contain concrete decisions or an explicit `"status":
"unknown"`. Do not hide missing evidence with empty objects.
