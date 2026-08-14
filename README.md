# Awesome AI Skills

Production-focused Agent Skills for AI engineering workflows. The repository
currently ships `rag-production-engineer`, a vendor-neutral skill for designing,
implementing, debugging, scaling, migrating, auditing, and operating RAG
systems.

## Available skill

### RAG production engineer

The skill covers ingestion, indexing, retrieval, grounded generation,
evaluation, tracing, latency, cost, security, fallback design, large datasets,
multi-tenancy, and multi-vendor migrations. It uses planning levels from `P0`
through `P3` so small work stays small while high-risk changes receive durable
plans, diagrams, audits, rollout gates, and rollback paths.

Read the source in the
[`rag-production-engineer` skill](skills/rag-production-engineer/SKILL.md).

## Install

Install the RAG skill from GitHub for supported agents:

```bash
npx skills@1.5.20 add Momen-Walied/awesome-ai-skills \
  --skill rag-production-engineer \
  --agent codex claude-code opencode antigravity
```

## Develop locally

List the discoverable skills:

```bash
npx skills@1.5.20 add . --list
```

Install the local checkout for supported agents:

```bash
npx skills@1.5.20 add . \
  --skill rag-production-engineer \
  --agent codex claude-code opencode antigravity
```

Installation from GitHub and the
[`skills.sh` directory listing](https://www.skills.sh/momen-walied/awesome-ai-skills/rag-production-engineer)
are available.

## Validate

Run the deterministic local suite:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile \
  scripts/run_skill_evals.py \
  skills/rag-production-engineer/scripts/*.py
python3 scripts/run_skill_evals.py evals/cases.jsonl --validate-only
```

Run the Agent Skills reference validator:

```bash
python3 -m pip install -r requirements-dev.txt
agentskills validate skills/rag-production-engineer
```

## Evaluate agent behavior

Export the portable prompts for any external agent runner:

```bash
python3 scripts/run_skill_evals.py \
  evals/cases.jsonl \
  --emit-prompts
```

Record one JSON object per line with `case_id`, `triggered`, and `response`,
then score the results:

```bash
python3 scripts/run_skill_evals.py \
  evals/cases.jsonl \
  --results path/to/recorded-results.jsonl
```

The scorer reports trigger precision and recall, routing and planning-level
compliance, required safety signals, prohibited claims, per-case failures, and
semantic checks that require manual review.

See [the evaluation strategy](evals/README.md) for the cross-agent matrix,
anti-overfitting rules, and the distinction between keyword smoke checks and
executable implementation evidence.

For the bounded configuration case, create a disposable repository before
opening your agent:

```bash
python3 scripts/prepare_eval_workspace.py \
  bounded-chunk-config \
  --output /tmp/rag-bounded-chunk-eval
cd /tmp/rag-bounded-chunk-eval
npx skills@1.5.20 add Momen-Walied/awesome-ai-skills \
  --skill rag-production-engineer \
  --agent opencode \
  --copy \
  --yes
opencode
```

Use the prompt printed by the setup script. This fixture prevents a workspace
mismatch from being mistaken for an implementation failure.

Use the same command shape with these migration resilience cases:

```text
migration-incompatible-embeddings
migration-without-cdc
migration-acl-capability-gap
stale-fallback-incident
planning-owner-decision-pressure
```

Each case creates a clean repository and prints its prompt and verification
commands. The first three require a `P3` migration plan; the stale-fallback
case exercises `OPERATE` behavior during an authorization-sensitive incident.
The owner-decision-pressure case must end at `AWAITING_DECISIONS` even when its
prompt demands autonomous completion.

Use `top-down-rag-implementation` to evaluate real implementation behavior. Its
fixture contains a layered retrieval service, an active Spec Kit artifact, and
three executable acceptance scenarios. The baseline intentionally fails the
exact-SKU scenario; a successful agent must edit the implementation and make
the full suite pass without weakening tenant isolation or dense rollback.

Use `ingestion-replay-revocation` for incremental indexing, checkpoints,
deletes, revocations, and idempotent replay. Use `stale-policy-fallback` for a
policy-sensitive timeout fallback that must fail closed when authorization
state is stale. Both fixtures preserve working paths so an agent must make a
bounded correction instead of replacing the architecture.

The runtime-safety fixtures extend this approach to `deadline-budget-propagation`,
`claim-citation-validation`, and `retrieved-tool-injection`. They test shared
deadlines, claim-level grounding, untrusted-content provenance, tenant-scoped
tool arguments, and observable denial without requiring a specific RAG
framework or provider.

The observability fixtures add `rag-telemetry-boundary` and
`grounded-slo-burn`. They test coherent trace propagation, redaction, metric
cardinality, degraded-trace retention, grounded outcome indicators, and
multi-window SLO burn without installing a monitoring vendor.

The retrieval-quality fixtures add `hybrid-rank-fusion` and
`retrieval-slice-regression`. They test fusion without comparing incompatible
raw scores, stable-ID deduplication, tenant-safe rollback, paired cohort
reporting, zero-tolerance authorization gates, and missing evaluation evidence
without installing a retrieval or evaluation vendor.

## Release policy

A release must pass unit tests, Python compilation, corpus validation, the
official Agent Skills validator, and local Skills CLI discovery. Major behavior
changes also require recorded outputs from multiple target agents and a review
of every failed evaluation case.
