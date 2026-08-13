# Vendor and integration strategy

Use this reference to choose products without leaking vendor semantics through
the entire application. Prefer capability fit and operational evidence over a
brand checklist.

## Define capability requirements

Write required capabilities before evaluating vendors.

For model and embedding providers, consider quality by language and domain,
context length, structured output, streaming, batch support, rate limits, data
handling, regions, version stability, latency, and price.

For search systems, consider dense and lexical search, metadata filters,
namespaces, hybrid fusion, reranking, update and delete semantics, consistency,
backups, encryption, regions, tenant isolation, observability, and restore time.

For evaluation and tracing systems, consider open telemetry formats, dataset and
experiment versioning, online evaluation, sampling, redaction, retention,
self-hosting, dashboards, alert export, and cost attribution.

## Place interfaces at stable boundaries

Use small domain contracts around capabilities the application owns.

```text
EmbeddingProvider.embed(texts, model_version)
Retriever.search(query, filters, limit, deadline)
Reranker.rank(query, candidates, limit, deadline)
Generator.generate(messages, schema, deadline)
TraceSink.record(event)
EvaluationRunner.run(dataset, configuration)
```

Return normalized results plus a namespaced provider metadata field. Preserve
raw provider responses in restricted diagnostic storage only when needed.

Do not flatten meaningful differences into a lowest-common-denominator API.
Expose capabilities explicitly and make unsupported behavior fail at startup or
configuration validation, not during a user request.

## Avoid speculative abstraction

Create a domain interface when one of these conditions is true:

- a second provider is required for resilience or migration;
- provider behavior would otherwise spread across business logic;
- testing needs a deterministic local implementation;
- compliance requires routing by region or data class;
- one provider cannot serve all workload tiers.

Do not implement every vendor in advance. Build one production implementation
and one test double, then add another provider from a real requirement.

## Compare complete operating cost

Benchmark providers with the same dataset, traffic model, filters, index size,
quality thresholds, and regions.

Include request price, tokens, storage, replicas, data transfer, observability,
minimum commitments, reindexing, support, migration, incident behavior, and team
operations. Compare cost per successful grounded answer.

## Plan fallback compatibility

Validate that a fallback preserves the required contract. Check embedding-space
compatibility, score semantics, filter behavior, reranking input limits, prompt
formats, structured output, tokenization, safety policy, regions, and data-use
terms.

Do not switch embedding providers at query time unless the index contains the
matching embedding space. A model fallback can also change answer quality,
latency, citations, and safety behavior, so evaluate it as a separate release.

## Run a state-correct migration

Treat a large index migration as an ordered state-replication problem, not a
bulk copy. Define one authoritative source, take a reproducible snapshot or
checkpoint, and record its change-stream watermark. Start change capture before
or at that watermark, backfill snapshot records, replay later mutations in
version order, then reconcile before any user-visible cutover.

Every mutation must carry a stable tenant, document, chunk, and source version.
Use idempotency keys and conditional writes so an older backfill record cannot
overwrite a newer live update. Represent deletes and permission revocations as
versioned tombstones until every target acknowledges them. Define propagation
objectives separately for content freshness and authorization revocation;
security-sensitive revocations normally require the stricter objective.

Prefer backfill from the source of truth. Use a vendor export only after proving
that it preserves identifiers, versions, source lineage, content, embedding
metadata, ACL state, and deletes. Reconcile counts by tenant and version, sample
record hashes, missing and extra identifiers, tombstones, and authorization
decisions. A global chunk count alone cannot prove convergence.

When vendor ACL semantics differ, resolve authorization into a canonical policy
decision, then compile that decision through one adapter per vendor. Do not pass
Vendor B filters to Vendor A or reuse a least-common-denominator filter. Apply a
defense-in-depth authorization check before context assembly, and test both
leakage and over-filtering. Deny retrieval when policy state or the selected
index's authorization watermark is stale.

Keep the old vendor hot only while it receives ordered mutations and meets the
same data and policy freshness gates. After dual-write stops, label the old
index retention-only; it is no longer a zero-data-loss failback. Separate the
hot failback window from the forensic retention and destruction windows.

Budget the fallback path from its own critical path:

```text
policy resolution
+ primary failure-detection deadline
+ fallback authorization adapter
+ fallback retrieval
+ context assembly
+ generation
+ validation
+ headroom
```

Measure or label each term. Do not describe an unexplained increment as the
fallback cost. Bound primary failure detection so the fallback still fits the
end-to-end deadline, and record the degraded retrieval behavior users receive.

## Separate retrieval and generation cutovers

Changing retrieval and generation in one program does not require changing them
in one production step. Use independent configuration flags and evaluate the
crossed combinations: old retrieval with old generation, new retrieval with old
generation, old retrieval with new generation, and new retrieval with new
generation. Establish retrieval acceptance before canarying the generation
change, unless an evidenced compatibility constraint makes separation
impossible.

Do not compare raw similarity scores across vendors. Inventory every consumer
of scores, top-k thresholds, confidence cutoffs, and empty-result rules. Prefer
rank-based comparison during shadowing, then calibrate vendor-specific
thresholds on labeled data before cutover.

## Account for migration cost

Separate steady-state cost from the migration envelope. The migration budget
must include source reads or export, backfill writes, optional re-embedding,
dual storage, dual-write, shadow queries, crossed evaluations, observability,
egress, and the hot failback window. Show formulas for one-time backfill cost,
incremental dual-run cost per day, and projected steady-state cost. Keep vendor
prices and effective throughput `UNKNOWN` until measured or verified from
first-party sources.

Keep duration and cost formulas dimensionally separate. For example:

```text
backfill_duration_seconds = total_chunks / effective_chunks_per_second
backfill_write_cost =
  total_billable_chunks / billing_unit_chunks * price_per_billing_unit
reembedding_cost =
  total_source_tokens / token_billing_unit * embedding_price_per_billing_unit
dual_run_cost_per_day =
  vendor_a_daily_storage + vendor_b_daily_storage
  + vendor_a_daily_writes + vendor_b_daily_writes
  + shadow_query_cost + observability_cost
```

Do not multiply elapsed seconds by a per-chunk price, and do not collapse two
vendors into `write volume * 2` unless both billing units and prices are proven
identical. Keep an unknown peak-to-average ratio or duty cycle independent from
peak QPS; use labeled sensitivity cases rather than deriving
`average = peak / N`.

## Integrate by category

Select current products from verified documentation at implementation time.
Common categories include:

- orchestration frameworks such as LangChain, LlamaIndex, Haystack, and
  Semantic Kernel;
- search systems such as PostgreSQL with pgvector, Elasticsearch, OpenSearch,
  Pinecone, Qdrant, Weaviate, Milvus, and managed cloud search;
- rerankers from model providers, search vendors, or locally hosted
  cross-encoders;
- evaluation systems such as Ragas, DeepEval, promptfoo, LangSmith, and custom
  deterministic harnesses;
- observability systems such as OpenTelemetry, Langfuse, LangSmith, Arize
  Phoenix, and existing application monitoring platforms;
- source connectors for object storage, databases, code hosts, wikis, document
  suites, chat systems, and event streams.

Use framework-native abstractions only when they do not obscure authorization,
deadlines, tracing, versioning, or provider-specific failure behavior.

## Record the decision

For each selected provider, record required capabilities, benchmark evidence,
data classification, region, limits, failure behavior, fallback, exit path,
owner, and review date.

Keep provider configuration versioned and inject it at composition boundaries.
Avoid provider SDK types in domain models and persisted business data.
