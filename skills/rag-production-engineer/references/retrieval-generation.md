# Retrieval and grounded generation

Use this reference to improve evidence discovery and answer construction. Debug
the pipeline in order: candidate recall, ranking, context assembly, generation,
and citation validation.

## Classify query behavior

Build query slices that reflect how retrieval fails, then evaluate every change
on each slice.

- semantic explanation and paraphrase;
- exact identifier, product code, person, or error message;
- time-sensitive or version-specific request;
- multi-constraint and multi-hop question;
- comparison across documents or entities;
- aggregation better served by SQL or analytics;
- conversational follow-up with missing standalone context;
- unsupported, ambiguous, adversarial, or permission-denied request.

Route deterministic structured queries to a database or API. Do not force all
knowledge access through vector similarity.

## Diagnose retrieval in order

Inspect failures with this sequence.

1. Verify the answerable source was ingested and authorized.
2. Verify parsing and chunk boundaries preserved the evidence.
3. Verify filters, namespaces, and version constraints admit the evidence.
4. Measure candidate recall at a broad `k`.
5. Inspect score distributions and duplicate candidates.
6. Measure precision and ranking after fusion or reranking.
7. Inspect context packing and token truncation.
8. Inspect generation only after the evidence path is sound.

### Guide a retrieval implementation

Trace the current classifier, policy filters, candidate sources, score fusion,
ranking, context assembly, and telemetry using real symbols and tests. Select a
representative failing query class and preserve the current route behind an
existing flag or boundary when rollback is required.

Guide the host to modify the stage that owns the measured failure and to reuse
the repository's retriever interfaces. Verify ranking, authorization, empty
results, trace route, and rollback behavior. Do not prescribe hybrid search,
reranking, or query expansion when a smaller exact-match or filter correction
passes the contract.

## Select retrieval techniques

Use techniques for a demonstrated query class or failure mode.

- Use dense search for semantic similarity and paraphrase.
- Use BM25 or another lexical method for rare terms, identifiers, and exact
  language.
- Use hybrid fusion when both query classes are material. Calibrate scores or
  use rank fusion instead of adding incomparable raw scores.
- Use metadata filters for authorization, time, language, source, document type,
  and version constraints.
- Use multi-query retrieval when alternate phrasings recover distinct evidence.
- Use decomposition when subquestions require independent retrieval.
- Use hypothetical-document retrieval only after evaluating domain-specific
  hallucination and latency effects.
- Use parent-child retrieval when small matching chunks need a larger coherent
  context.
- Use graph or relationship traversal when explicit connections, not semantic
  similarity, determine the answer.

Limit query expansion and retrieval fan-out. Run independent calls concurrently
within one shared deadline, then deduplicate by stable chunk or parent ID.

## Apply reranking deliberately

Retrieve a broad candidate set, then rerank a smaller bounded set when candidate
recall passes but early precision does not.

Measure reranker quality by query slice and account for added latency, cost,
context length, and provider failure. Preserve the original retrieval score and
the reranker score in traces. Define a pass-through fallback that returns the
best original ranking when reranking fails or times out.

## Assemble context

Build context from evidence, not from raw top-k order alone.

- Deduplicate near-identical chunks and overlapping windows.
- Group related child chunks under their parent when it improves coherence.
- Preserve source and section boundaries with explicit identifiers.
- Prefer diversity across useful evidence over repeated copies of one passage.
- Allocate tokens based on query needs and evidence value.
- Keep untrusted document content separated from system instructions.
- Record which retrieved candidates were included, excluded, or truncated.

Compression is a lossy retrieval stage and requires evaluation. Never compress
away qualifiers, units, dates, exceptions, or attribution.

## Generate grounded answers

Tell the model to answer from supplied evidence, cite the supporting source for
material claims, expose uncertainty, and abstain when evidence is insufficient
or conflicting.

Validate citation identifiers against the supplied context. For high-risk use
cases, verify that each claim is entailed by its cited passage and route low
confidence to a safe response or human review.

Use structured output when downstream code consumes the result. Validate the
schema and treat malformed output as a bounded failure, not as free text.

### Guide citation validation changes

Trace claims from generated structure to the exact authorized context units
that support them. Distinguish a citation identifier that merely exists from a
citation that entails the claim. Preserve immutable source and chunk versions
through validation and the final response.

Guide the host to reuse the current answer schema and validator. Test supported
claims, valid IDs with unrelated evidence, missing citations, citations outside
the supplied context, conflicting evidence, and the configured abstention or
review path. Use deterministic fact or identifier checks where possible and a
calibrated semantic judge only when entailment cannot be expressed reliably.

## Use agentic retrieval sparingly

Use an agent only when runtime decisions cannot be represented reliably as a
small static router or deterministic workflow. Bound tool choices, steps,
tokens, time, and spend.

Trace every tool call and preserve intermediate evidence. Prevent the agent
from widening tenant scope, bypassing filters, or treating retrieved content as
instructions. Define a deterministic fallback for planning failure.
