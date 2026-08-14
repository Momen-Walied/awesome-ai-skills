# Reliability and security

Use this reference to keep retrieval safe and useful during missing evidence,
dependency failure, malicious content, stale data, and tenant isolation errors.

## Classify failure states

Represent failure states explicitly so the response policy can distinguish
them.

- No authorized evidence exists.
- Evidence exists but retrieval confidence is low.
- Evidence is conflicting, stale, or from the wrong version.
- A provider timed out, rejected the request, or returned malformed output.
- A policy denied retrieval or generation.
- The index is incomplete, rebuilding, or unavailable.
- A downstream citation or schema validation failed.

Do not turn these states into the same generic apology. Return safe behavior and
machine-readable reason codes where the application contract supports them.

## Design fallback ladders

Define fallbacks per stage and stop when evidence quality becomes unsafe.

An example retrieval ladder is primary hybrid search, dense-only search,
lexical-only search, a validated cache, and then abstention. An example model
ladder is the primary model, a compatible secondary provider, a smaller local or
hosted model for bounded tasks, and then a non-generative evidence response.

Fallbacks must preserve authorization, citation, freshness, and output-schema
contracts. A fast fallback that answers from unauthorized or unsupported
content is not a valid fallback.

Never describe an authorization incident response as fail-open. Fail closed on
missing, malformed, stale, or divergent policy state. After an index stops
receiving ordered content and permission mutations, classify it as
retention-only and remove it from the fallback ladder.

Record fallback reason, selected path, quality limitations, and user-visible
degradation. Test each fallback under load.

## Bound remote calls

Set connection and operation timeouts below the remaining request deadline.
Retry only idempotent transient failures. Use jitter, attempt limits, circuit
breakers, and bulkheads to prevent cascading failures.

Respect provider rate-limit signals and apply admission control before queues
grow without bound. Avoid automatic cross-provider retries when data residency,
privacy, or model behavior differs.

## Enforce authorization

Resolve tenant and user policy before retrieval. Push mandatory filters into
every retrieval path, including lexical search, vector search, caches, graph
traversal, and fallback providers.

Test cross-tenant access with adversarial cases and verify an unauthorized
result rate of zero. Use deny-by-default behavior when policy metadata is
missing, malformed, or stale.

Keep authorization attributes separate from model-generated metadata. The model
cannot grant access.

At large corpus sizes, do not copy unbounded user and group lists onto every
chunk by default. Measure principal cardinality and permission churn, then
choose a bounded representation such as tenant plus document policy-set IDs or
precomputed authorization tokens that the retrieval provider can filter. Keep
the authoritative document policy outside the vector index and add a
defense-in-depth authorization check before context assembly.

Distinguish logical isolation from physical isolation. A namespace, collection,
or index per tenant does not necessarily require a separate compute fleet per
tenant; verify the provider's routing, filter, backup, quota, and noisy-neighbor
semantics before making a cost or security claim.

### Guide a policy-sensitive fallback change

Trace policy resolution and policy-version propagation before tracing the
fallback. Model primary success, dependency failure with a fresh fallback,
dependency failure with stale policy, cross-tenant candidates, and recovery.
Require the host to preserve the primary route and to make unsafe fallback
states observable while returning denial or abstention.

Prefer a local policy-version or freshness check at the existing routing
boundary. Do not add a second authorization system, duplicate the policy store,
or make broad provider abstractions to repair one missing gate.

## Defend against untrusted content

Treat retrieved documents as untrusted data, not instructions. Separate them
from system and developer instructions with explicit boundaries and labels.

Detect or contain attempts to override policy, reveal secrets, call tools, or
redirect retrieval. Allowlist tools and arguments, validate URLs and file paths,
and require confirmation for consequential actions outside the RAG answer flow.

Use source trust, provenance, and content policy as retrieval or ranking signals
when the domain requires them. Do not rely on a prompt alone as the security
boundary.

### Guide tool-call security changes

Trace the origin of every proposed action from user intent, application policy,
model output, and retrieved content to the execution gateway. Retrieved text
can supply data but never grants authority, expands tenant scope, selects a
consequential tool, or supplies unrestricted arguments.

Guide the host to enforce provenance, tool allowlists, argument schemas,
tenant-scoped resource checks, and confirmation at the existing tool boundary.
Test direct and indirect prompt injection, an allowlisted tool proposed only by
a document, argument smuggling, a valid user-authorized call, denial telemetry,
and that denied calls never reach the executor. Keep prompt instructions as
defense in depth, not the authorization mechanism.

## Protect sensitive data

Classify source data, prompts, traces, evaluation sets, and caches. Apply least
privilege, encryption, retention, regional controls, deletion workflows, and
audit logging.

Redact or tokenize personal and secret values before third-party calls unless
the approved data flow explicitly permits them. Verify that deletion propagates
to indexes, caches, replicas, backups, and evaluation samples according to the
required retention policy.

## Plan recovery

Back up configuration, source checkpoints, and indexes when rebuilding within
the recovery objective is not guaranteed. Test restore, replay, reindex,
provider failover, and rollback procedures.

Use reconciliation to detect missing, duplicate, orphaned, and undeleted index
records. Keep the previous index and configuration available through a bounded
release window.
