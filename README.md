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

Installation from GitHub works now. The `skills.sh` directory listing is pending
upstream indexing in
[`vercel-labs/skills#1951`](https://github.com/vercel-labs/skills/issues/1951).

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
```

Each case creates a clean repository and prints its prompt and verification
commands. The first three require a `P3` migration plan; the stale-fallback
case exercises `OPERATE` behavior during an authorization-sensitive incident.

## Release policy

A release must pass unit tests, Python compilation, corpus validation, the
official Agent Skills validator, and local Skills CLI discovery. Major behavior
changes also require recorded outputs from multiple target agents and a review
of every failed evaluation case.
