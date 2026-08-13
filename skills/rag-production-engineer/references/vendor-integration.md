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
