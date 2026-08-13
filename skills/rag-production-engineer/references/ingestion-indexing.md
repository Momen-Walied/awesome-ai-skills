# Ingestion and indexing

Use this reference to design a traceable, idempotent pipeline from source data
to searchable units. Optimize for source fidelity, incremental change, safe
reprocessing, and rollback before optimizing throughput.

## Preserve identity and lineage

Assign stable identifiers at each level and carry them through index records,
citations, evaluations, and traces.

- `source_id` identifies the connector or source system.
- `document_id` remains stable across content revisions.
- `document_version` changes when retrieval-relevant content or policy changes.
- `chunk_id` is deterministic for unchanged content and chunking configuration.
- `tenant_id` and access attributes are mandatory where isolation applies.
- `index_version`, `parser_version`, `chunker_version`, and `embedding_version`
  explain how a record was produced.

Store source location, title, section path, timestamps, content checksum, and
deletion state. Make every answer traceable to an immutable document version.

## Parse for meaning

Preserve document structure that can improve retrieval or citations. Detect and
handle headings, paragraphs, lists, tables, code blocks, captions, page numbers,
and attached metadata.

Keep the raw source or a durable pointer to it. Store normalized text separately
from extraction artifacts so parser upgrades do not destroy evidence.

Measure extraction coverage and route low-confidence parses for review. OCR,
table extraction, and layout reconstruction need their own quality samples.

## Select a chunking strategy

Match chunks to expected evidence units and preserve parent context.

- Use heading-aware chunks for structured documentation and policies.
- Use paragraph or semantic boundaries for prose with variable section sizes.
- Use table-aware chunks that retain headers, units, and row context.
- Use symbol-aware chunks for code, including file and enclosing symbol paths.
- Use parent-child chunks when precise retrieval needs broader answer context.
- Use overlap only when boundary loss is observed; excessive overlap increases
  cost, duplicates results, and distorts evaluation.

Evaluate chunking on retrieval and citation quality. Token count alone is not a
quality metric.

## Build an idempotent pipeline

Separate discovery, fetch, parse, normalize, authorize, chunk, embed, and index
stages. Give each stage an input contract, output contract, retry policy, and
dead-letter path.

Use content hashes and deterministic IDs to skip unchanged work. Write index
updates with upsert semantics and process deletions explicitly. Make replay safe
after partial failure.

For incremental synchronization, use the strongest change signal the source
supports:

1. Prefer a transaction log or change data capture stream.
2. Use source webhooks or event feeds when delivery can be reconciled.
3. Use modified timestamps with overlap and periodic full reconciliation.
4. Use full scans only when no reliable incremental signal exists.

## Scale the data plane

Partition work by a stable key such as tenant or source, while accounting for
skew. Use bounded queues and backpressure so embedding or index outages do not
exhaust memory or overload sources.

Batch embeddings within provider token and request limits. Tune batch size from
measured throughput, latency, failure rate, and retry cost. Rate-limit each
provider and tenant independently when noisy-neighbor behavior matters.

Track these pipeline metrics:

- discovery lag and end-to-end freshness lag;
- documents and chunks processed per minute;
- unchanged, added, updated, deleted, and failed records;
- parse coverage and low-confidence extraction rate;
- embedding and indexing latency, errors, retries, and cost;
- queue depth, oldest message age, and dead-letter volume;
- indexed record count compared with the source-of-truth count.

## Version and migrate indexes

Treat parser, chunking, metadata, and embedding changes as versioned migrations.
Build a new index or namespace, evaluate it against the current version, shadow
traffic when useful, then switch through a reversible alias or configuration.

Do not mix incompatible embedding spaces in one searchable field. Use dual
writes only for a bounded migration window and monitor divergence. Retain the
previous version until rollback and citation reproducibility requirements pass.

When a source has no CDC, don't infer zero-loss changes from periodic snapshots.
Write the business mutation and its outbox event in the same transaction, or use
an equivalent atomic source boundary. Activate that capture before the bootstrap
snapshot so mutations during extraction and backfill have an ordered replay
position. Route background jobs, admin tools, and integrations through the same
boundary. If any path can bypass it, require a bounded write freeze or classify
zero-downtime cutover as blocked. Capture hard deletes and permission
revocations as durable versioned events before source state disappears.
