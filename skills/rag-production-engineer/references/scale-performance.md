# Scale, latency, and cost

Use this reference to engineer performance from workload measurements. Optimize
tail latency and successful-answer economics, not isolated microbenchmarks.

## Model capacity

Estimate capacity for the data and query planes independently.

For the data plane, measure source scan rate, parse throughput, embedding tokens
per second, index write rate, queue growth, and freshness lag. For the query
plane, measure arrival rate, concurrency, service time, fan-out, model tokens,
and dependency quotas.

Test steady traffic, expected peaks, skewed tenants, burst recovery, and one
degraded provider. Include warm-up, connection pools, cache state, and realistic
document sizes.

## Control latency

Assign a deadline to the complete request and derive shorter deadlines for each
stage. Propagate cancellation so abandoned or timed-out requests stop consuming
capacity.

Use these techniques only where measurements support them:

- run independent retrieval sources concurrently;
- batch offline embeddings and compatible online operations;
- reuse connections and keep clients long-lived;
- cap query expansion, candidate counts, reranker inputs, and answer tokens;
- cache immutable transformations and version cache keys;
- precompute stable enrichment and document summaries;
- use approximate nearest-neighbor parameters that meet recall targets;
- stream generation to improve time to first token, while still measuring total
  completion time;
- isolate slow tenants or workloads with queues, admission control, or pools.

Retries increase tail latency and load. Retry only transient, idempotent
operations, use exponential backoff with jitter, respect the request deadline,
and cap attempts.

### Guide a performance implementation

Require a reproducible baseline and trace the measured critical path before
editing. Choose one bottleneck and one controlled variable, preserve the old
route as the comparison, and define the load shape, warm-up, sample count, and
acceptance threshold. Guide the host to use the repository's benchmark or load
tool rather than inventing a synthetic harness when one already exists.

Reject improvements that move work outside the measured window, weaken recall
or authorization, increase retries, or omit tail percentiles. Add architecture
only when profiling shows that a local change cannot meet the gate.

## Design caches with semantics

Define the cache unit, key, validity, tenant scope, and invalidation event
before adding a cache.

- Cache parsed and normalized content by source version.
- Cache embeddings by normalized content hash and embedding version.
- Cache retrieval by query, filters, index version, and authorization scope.
- Cache final answers only when freshness, personalization, citations, and
  policy semantics are safe.

Track hit rate, saved latency, saved cost, staleness, and invalidation failures.
A low-value cache adds state and incident paths without improving the outcome.

## Scale storage and search

Estimate vector memory, metadata size, index overhead, replicas, and migration
headroom. Benchmark with representative filters because filtered search can
change recall and latency substantially.

Partition by a key that supports routing and isolation. Tenant partitioning can
improve security and deletion behavior but may waste capacity for small tenants.
A shared index can improve utilization but needs strict filter enforcement and
skew controls.

Add replicas for read throughput and availability only after measuring write
and consistency effects. Plan compaction, snapshots, restore testing, and index
rebuild duration.

## Control cost

Calculate cost by successful grounded answer and by workload slice.

Before reporting a capacity, latency, duration, or cost result, write the
calculation with named inputs and units. At minimum:

- convert rates to the same time unit, such as
  `answers/day = QPS * utilization * 86,400 seconds/day`;
- calculate workload cost as
  `period cost = successful answers * cost/successful answer`;
- calculate migration duration as
  `items / effective sustained throughput`, including retry, quota, and
  throttling assumptions;
- state whether bytes use decimal or binary units and whether prices are per
  token, request, hour, operation, or stored unit;
- recompute the result independently and verify its order of magnitude.

Label inputs as `MEASURED`, `ESTIMATED`, `PROPOSED`, or `UNKNOWN`. Give a range
when effective throughput, utilization, compression, cache hit rate, or vendor
limits are unknown. Treat zero headroom as a failed capacity gate, not a viable
steady-state plan. When exact vendor prices materially affect a decision, use
current first-party pricing and record the source date.

For managed services, record the billed data-size definition, region, plan,
rate limits, and whether index overhead is included in billable storage. For
self-managed services, do not publish a currency estimate without instance or
node counts, CPU, memory, disk, replicas, utilization, and unit prices. Use
`UNKNOWN` plus the sizing formula when those inputs are unavailable.

Include source extraction, embedding, index storage and operations, reranking,
model input and output tokens, observability, network transfer, replicas, and
engineering operations.

Common controls include smaller candidate sets after recall testing, conditional
reranking, context deduplication, answer-length limits, model routing, batching,
semantic caching, retention controls, and tiered service levels.

Do not optimize unit price while increasing retries, low-quality answers, or
operator burden. Include failure and reprocessing costs in comparisons.

## Prevent noisy neighbors

Apply per-tenant rate limits, concurrency limits, budget controls, queue quotas,
and observability. Detect skew in corpus size, query volume, context size, and
expensive routes.

Use admission control and degradation before saturation. Preserve capacity for
health checks, policy decisions, and high-priority workloads during incidents.
