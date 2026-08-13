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

## Install from a local checkout

List the discoverable skills:

```bash
npx skills@1.5.20 add . --list
```

Install the RAG skill for supported agents:

```bash
npx skills@1.5.20 add . \
  --skill rag-production-engineer \
  --agent codex claude-code opencode antigravity
```

After the repository is public, replace `.` with its GitHub `owner/repository`
identifier. The same public source becomes discoverable through
[skills.sh](https://skills.sh/).

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
compliance, required safety signals, prohibited claims, and per-case failures.

## Release policy

A release must pass unit tests, Python compilation, corpus validation, the
official Agent Skills validator, and local Skills CLI discovery. Major behavior
changes also require recorded outputs from multiple target agents and a review
of every failed evaluation case.
