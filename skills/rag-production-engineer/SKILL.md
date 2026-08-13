---
name: rag-production-engineer
description: >-
  MANDATORY: invoke this skill before any repository or reference tool call for
  production RAG work. Design, implement, review, debug, scale, migrate, and
  operate RAG systems. Always use it for repository work involving RAG ingestion
  or retrieval, including small config and test changes to chunk size,
  chunk overlap, parsing, embeddings, indexing, hybrid search, reranking, or
  grounded generation. Load it before
  repository exploration, planning, or edits. After invocation, the next visible
  work update must start with mode, then
  planning level, and execution ledger before explanatory prose. Also trigger
  for evaluation, tracing, monitoring, latency, cost, fallbacks, security,
  multi-tenancy, large-scale data, incidents, vendor selection, and multi-vendor
  migration. Enforce inspection, reviewed plans, tracked execution, measurable
  baselines, phase gates, and fresh verification. Do not use for prompting or
  fine-tuning tasks without external retrieval.
license: MIT
metadata:
  author: awesome-ai-skills
  version: "0.1.10"
---

# RAG production engineer

Deliver the smallest RAG system that meets measured quality, latency, cost,
freshness, security, and reliability targets. Control the work with explicit
modes, tracked tasks, evidence gates, and bounded fallbacks. Leave every answer
and design decision explainable. The instructions are portable across Agent
Skills clients. Bundled Python utilities require Python 3.11 or newer.

## Run the mandatory preflight

Before any repository inspection, reference read, delegated task, or other tool
call, publish `Mode: <MODE>`, `Planning level: P0|P1|P2|P3`, and the execution
ledger required by the scope. This preflight is the first work update, not a
summary added after exploration.

After the skill invocation, make the next visible work update begin with these
literal lines, in this order: `Mode:`, `Planning level:`, and `Execution
ledger:`. Do not place routing prose or the ledger before those declarations.

## Route the task

Select one primary mode before doing substantial work. Add a secondary mode
only when the request genuinely crosses boundaries.

| Mode | Use when | Required result |
| --- | --- | --- |
| `DESIGN` | Creating or changing architecture | Decision-ready design |
| `IMPLEMENT` | Building an approved behavior | Working, verified changes |
| `DEBUG` | Investigating incorrect or failed behavior | Proven root cause and fix |
| `OPTIMIZE` | Improving quality, latency, or cost | Baseline comparison |
| `MIGRATE` | Changing a model, index, framework, or vendor | Reversible migration |
| `AUDIT` | Reviewing readiness, security, or architecture | Prioritized findings |
| `OPERATE` | Handling an incident or degraded service | Mitigation and recovery |

Apply these routing rules:

- For `DESIGN`, inspect the current system and produce decisions, gates, and
  delivery phases. Do not implement unless the user requests implementation.
- For `IMPLEMENT`, continue through code changes and verification when the
  requested target exists. If a named existing target is absent, apply the
  workspace-mismatch hard gate instead of inventing a replacement.
- For `DEBUG`, reproduce and locate the failure before proposing a fix.
- For `OPTIMIZE`, preserve the current configuration as the baseline and change
  one meaningful variable at a time.
- For `MIGRATE`, define compatibility, shadowing or dual-run behavior, cutover,
  rollback, and old-state retirement. For a provider or index migration, also
  prove ordered data convergence, authorization equivalence, score-consumer
  compatibility, bounded fallback freshness, and independent retrieval and
  generation rollout controls.
- For `AUDIT`, lead with findings ordered by severity and attach evidence to
  every finding. Do not mutate the system unless the user also requests fixes.
- For `OPERATE`, protect data and availability first, preserve evidence, then
  diagnose and recover.

## Control execution

For any task with three or more meaningful actions, create a task-specific
execution ledger before starting. Use the host agent's native todo or plan tool
when available; otherwise maintain a compact Markdown checklist.

Begin the first work update with `Mode: <MODE>` and one sentence explaining the
route. Create the ledger immediately after that line and before substantive
analysis. In a response-only environment with no separate progress updates,
make `Mode` and `Execution ledger` the first two sections of the response.
An action list written after the analysis does not satisfy this requirement.

Follow this state protocol:

1. State the selected mode and its required result.
2. Create four to eight outcome-oriented tasks with explicit completion
   criteria.
3. Mark exactly one task `in_progress`.
4. Perform the task and collect its required artifact or command output.
5. Compare the evidence with the completion criterion.
6. Mark the task `completed` only when the criterion passes.
7. Update status immediately. Never batch-complete tasks at the end.
8. Add a new task when evidence reveals necessary work outside the ledger.

Do not copy the full RAG lifecycle into every ledger. Track only the phases the
selected mode and scope require. Skip the ledger for a short factual answer
that needs fewer than three actions.

Before the final response, close the ledger with evidence for every completed
item. Keep blocked or deferred items open and name the missing decision or
failed gate. In a response-only task, include this closed ledger in the final
response so execution remains auditable.

Use this fallback format when the host has no task tool:

```text
- [x] Inspect current path — evidence: files and configuration identified
- [>] Measure baseline — done when quality, latency, and cost are recorded
- [ ] Implement the smallest justified change — done when tests pass
- [ ] Verify under failure conditions — done when fallback evidence exists
```

Treat discoverable facts as your responsibility. Inspect code, configuration,
schemas, logs, traces, datasets, and provider documentation before asking the
user. Ask only for unavailable business decisions, credentials, approvals, or
facts that materially change the design. Proceed with labeled assumptions when
the missing information is noncritical.

## Pass the planning gate

Choose the planning level after initial inspection. Match planning effort to
blast radius, uncertainty, and reversibility.

| Level | Use when | Required artifact |
| --- | --- | --- |
| `P0` | Factual answer or read-only inspection with no repository mutation | Direct answer |
| `P1` | Bounded code, config, test, or documentation change | Proposed plan in chat |
| `P2` | Cross-component or production behavior change | Reviewed Markdown plan |
| `P3` | Migration, high-risk, large-scale, or multi-vendor program | Staged Markdown plan |

For `P1`, put `Mode: <MODE>` and `Planning level: P1` in the first work update,
followed by a concise proposed plan before editing. When the task has three
actions such as locate, update, and verify, use those actions as the execution
ledger. Do not replace these declarations with a retrospective summary because
the change appears trivial.

Any requested repository mutation starts at `P1`, including a one-line value
change. Never downgrade config plus focused-test work to `P0` because the
behavioral change has only one variable.

For `P1`, use direct repository search and file-reading tools. Do not delegate
to planning or exploration subagents for a bounded local change. When a root
inspection plus one repository-wide path and content search proves that named
existing targets are absent, apply the workspace-mismatch gate immediately;
additional speculative searches add latency without improving the evidence.

Require `P2` or `P3` for new architectures, data or index migrations, ACL or
security changes, provider changes, multi-vendor routing, distributed scaling,
major retrieval redesigns, and performance work that changes production
capacity or service-level objectives. Use `P3` for large-scale greenfield
systems and when the work needs phased delivery, dual-running, cutover,
rollback, or retirement of old state.

For `P2` and `P3`, read
[planning-protocol.md](references/planning-protocol.md), then follow this gate:

1. Inspect the repository, runtime evidence, and existing documentation.
2. Draft the current state, target state, delta, and implementation slices.
3. Add diagrams that clarify architecture or sequence.
4. Audit the draft against requirements, evidence, risk, and operability.
5. Resolve discoverable gaps yourself.
6. Ask the user only for unresolved high-impact decisions. Include your
   recommendation and the consequence of each option.
7. Revise the plan and mark assumptions, decisions, and open questions.
8. Save the final Markdown plan using the repository's planning convention, or
   `docs/plans/YYYY-MM-DD-<slug>.md` when no convention exists.
9. Run `scripts/validate_plan_document.py <plan.md> --level P2|P3` and resolve
   every structural failure before marking the plan `READY`.

For `P3`, include a dedicated `Capacity, latency, and cost budgets` section.
Normalize workload rates across time units, show formulas and units, reserve
latency headroom, and label every non-user-provided input. Use sensitivity
ranges when traffic shape, throughput, token volume, or price is unknown. Keep
the document status and plan-audit result identical.

Use `assets/rag-plan-template.md` when the repository has no stronger planning
template. Replace every `UNKNOWN` that can be discovered before validation.

Do not modify the target system before this gate passes. When the user already
requested implementation, continue after the audited plan is final unless a
high-impact decision remains open, the action needs separate approval, or the
user requested a plan-approval checkpoint. When the user requested planning
only, stop after delivering the plan.

The plan may be long when the system is large. Keep it navigable through clear
sections, scoped diagrams, decision tables, and independently verifiable
delivery slices. Never trade decision completeness for artificial brevity.

## Enforce the hard gates

These gates prevent plausible-looking work from replacing engineering proof.

```text
NO OPTIMIZATION WITHOUT A RECORDED BASELINE.

NO RERANKING, GRAPH RAG, OR AGENTIC RAG WITHOUT A NAMED FAILURE,
AN EVALUATION GATE, AND A ROLLBACK PATH.

NO PRODUCTION-READY CLAIM WITHOUT FRESH QUALITY, LATENCY,
FAILURE, AND SECURITY EVIDENCE.

NO MULTI-VENDOR FAILOVER CLAIM WITHOUT COMPATIBLE DATA,
POLICY, INDEX, AND OUTPUT CONTRACTS.

NO ZERO-DOWNTIME MIGRATION CLAIM WITHOUT A SNAPSHOT WATERMARK,
ORDERED MUTATIONS, TOMBSTONES, REVOCATION CONVERGENCE, AND RECONCILIATION.

NO CAPACITY, LATENCY, DURATION, OR COST CLAIM WITHOUT EXPLICIT
UNITS, INPUTS, FORMULA, ASSUMPTIONS, AND A RECOMPUTATION CHECK.

NO SUBSTITUTE FILES WHEN A REQUESTED EXISTING CONFIGURATION,
TEST, OR APPLICATION TARGET IS ABSENT. REPORT WORKSPACE MISMATCH AND STOP.
```

Apply these rules throughout the task:

- Treat retrieval quality, answer quality, latency, cost, and reliability as
  separate dimensions. Never hide one behind an aggregate score.
- Put access control before or inside every retrieval path. Deny by default
  when authorization metadata is missing, malformed, or stale.
- Preserve stable source, document, chunk, tenant, and version identifiers from
  ingestion through citations, evaluations, and traces.
- Instrument a stage before optimizing it. Report p50, p95, and p99 instead of
  averages alone.
- Label unmeasured values as `ESTIMATED` or `PROPOSED`. Do not present a
  derived value until its units and arithmetic have been checked independently.
- Do not invent a peak-to-average ratio, workload duty cycle, vendor price, or
  migration rate. Keep it `UNKNOWN` and show a sensitivity calculation.
- Keep domain interfaces vendor-neutral at meaningful boundaries. Add a second
  implementation only for a real resilience or migration requirement.
- Bound every remote call with a deadline, retry policy, circuit behavior, and
  degradation result.
- Prefer positive execution instructions. Use prohibitions only for hard safety
  or evidence gates.

## Execute the gated workflow

Run only the phases required by the selected mode, but preserve their order.
Return to an earlier phase whenever its evidence becomes invalid.

### Phase 1: Inspect and frame

Inspect the existing system before recommending products or changes. Identify
the user outcome and the cost of a wrong, incomplete, stale, or slow answer.

When the requested application file, configuration, or test is absent after a
repository-wide search, report a workspace mismatch and stop that implementation
path. Do not create substitute application artifacts in a skill, documentation,
or unrelated repository unless the user explicitly requested a greenfield
scaffold in their latest request. Words such as `fixture-only`, `existing`, or
`documented` do not grant permission to create missing targets. Do not reason
past this gate because creating a replacement appears harmless or helpful. Ask
for the correct repository or path; for skill evaluation, use a disposable
fixture outside the product tree.

Capture this workload profile:

- use case and representative query classes;
- required evidence, citation, and abstention behavior;
- corpus bytes, documents, chunks, growth, and update rate;
- query rate, concurrency, traffic shape, and tenant skew;
- quality thresholds by query and risk class;
- p50, p95, and p99 latency objectives;
- cost budget per successful grounded answer and monthly ceiling;
- freshness, availability, recovery, privacy, and residency requirements;
- authorization model, data sensitivity, and regulatory constraints;
- current stack, versions, team capacity, and migration constraints.

Read [architecture.md](references/architecture.md) and
[scale-performance.md](references/scale-performance.md) for architecture or
scaling work.

**Completion criterion:** Record each dimension as measured, estimated, not
applicable, or unknown. Identify which unknowns can change the design.

### Phase 2: Establish the baseline

Build or inspect the least complex end-to-end path that can be evaluated. Keep
the current production configuration unchanged as the comparison baseline.

Default to one parsing path, structure-aware chunks, one embedding model,
authorization-filtered dense retrieval, direct context assembly, grounded
generation, and citations. Add lexical retrieval to the baseline when exact
identifiers, names, codes, or domain terms are material query classes.

Define representative evaluation cases, slices, metrics, and acceptance
thresholds before tuning. Read [evaluation.md](references/evaluation.md) and
run `scripts/evaluate_retrieval.py` when ranked document IDs are available.
Use `assets/retrieval-evaluation.schema.json` to produce compatible JSONL rows.

**Completion criterion:** Store reproducible baseline quality, latency, cost,
error, and fallback results with dataset, code, configuration, model, embedding,
prompt, and index versions. If measurement is impossible, record the exact
instrumentation or dataset gap as the next task.

### Phase 3: Diagnose and choose

Locate the failing stage before selecting a technique. Diagnose source coverage,
parsing, chunking, authorization filters, candidate recall, ranking, context
assembly, generation, and citation validation in that order.

Read the minimum references needed for the observed problem:

- Read [ingestion-indexing.md](references/ingestion-indexing.md) for parsing,
  lineage, synchronization, versioning, and large-data ingestion.
- Read [retrieval-generation.md](references/retrieval-generation.md) for hybrid
  search, reranking, query transformation, hierarchy, generation, and citations.
- Read [observability.md](references/observability.md) for trace hierarchy,
  metrics, dashboards, alerts, and redaction.
- Read [reliability-security.md](references/reliability-security.md) for ACLs,
  fallbacks, recovery, prompt injection, and sensitive data.
- Read [vendor-integration.md](references/vendor-integration.md) for provider
  selection, stable interfaces, compatibility, and migration.

Select the lowest architecture level that can pass the failed gate:

1. Use no RAG when the task needs no external or changing knowledge.
2. Use direct lookup for small, deterministic, structured knowledge.
3. Use authorization-filtered dense RAG for semantic document retrieval.
4. Add lexical retrieval for measured exact-match recall failures.
5. Add reranking when broad candidate recall passes but early precision fails.
6. Add decomposition or multi-query retrieval for validated composite queries.
7. Add parent-child or hierarchical retrieval when precise chunks need broader
   answer context.
8. Add graph-assisted retrieval when explicit relations drive validated
   multi-hop answers.
9. Add agentic retrieval only when runtime tool or strategy choice cannot be
   expressed as a small deterministic router.
10. Distribute a plane only when measured scale requires independent capacity,
    partitioning, or failure isolation.

For a greenfield target, keep reranking, semantic caching, query expansion, and
other optional stages behind their measured upgrade triggers. Large scale alone
does not establish the quality failure or cache semantics required by the hard
gates.

**Completion criterion:** Name the failed metric or failure mode, the smallest
intervention that targets it, alternatives rejected, expected effect, new risk,
evaluation gate, and rollback path.

### Phase 4: Implement or specify

Produce the artifact required by the selected mode. Follow established project
patterns and keep each change independently testable.

Before changing code or configuration, confirm the required planning level has
passed. Treat the audited Markdown plan as the execution source of truth for
`P2` and `P3`; update it when evidence changes a decision, scope, interface, or
rollout step.

For `IMPLEMENT`, change the smallest coherent surface, add tests at public
boundaries, instrument changed stages, and preserve compatibility or provide a
migration. For `DESIGN`, define interfaces, data contracts, stages, ownership,
budgets, rollout, and measurable acceptance gates. For `AUDIT`, record findings
without expanding into an unsolicited redesign.

For a machine-checkable design, create JSON matching the plan contract in
[architecture.md](references/architecture.md), then run
`scripts/validate_rag_plan.py`.

**Completion criterion:** Produce reviewable code, configuration, or a
decision-ready design. Remove placeholders, resolve internal inconsistencies,
and trace every requirement to an implementation task or explicit deferral.

### Phase 5: Instrument and harden

Create one trace per request and one span per material stage. Include retrieved
IDs, scores, filters, versions, latency, tokens, cost, errors, and fallback
decisions without logging sensitive content by default.

Enumerate empty evidence, low confidence, stale or conflicting evidence,
dependency failure, rate limits, malformed output, policy denial, incomplete
indexes, and citation failure. Define a bounded response and owner for each
relevant state.

Use `scripts/analyze_traces.py` for compatible JSONL trace exports.
Use `assets/trace-span.schema.json` when creating a new export adapter.

**Completion criterion:** Trace one successful path and each critical failure
path. Verify authorization and output contracts remain intact through every
fallback and vendor route.

### Phase 6: Verify and compare

Run fresh tests, evaluations, benchmarks, and failure exercises that directly
prove the requested result. Read complete outputs and record exit codes and
metric deltas.

Verify the relevant gates:

- retrieval and answer quality on representative slices;
- missing, conflicting, stale, and unauthorized evidence behavior;
- p50, p95, and p99 end-to-end and stage latency under expected load;
- cost per successful grounded answer;
- provider timeout, rate-limit, malformed-response, and outage behavior;
- idempotent ingestion, deletion, index rollback, and version migration;
- citation lineage to an immutable authorized source version;
- dashboards, alerts, ownership, and recovery runbooks.

**Completion criterion:** Map every completion claim to fresh evidence. Report
the actual status and remaining risk when a gate fails or cannot run.

## Handle blockers and failed attempts

Preserve evidence and change direction deliberately instead of repeating
plausible fixes.

- When reproduction fails, improve observability and collect another sample.
- When two interventions fail, revisit the diagnosis and compare with a known
  working path before attempting another change.
- When three interventions fail for the same symptom, question the architecture
  or assumption set and stop stacking fixes.
- When authorization is uncertain, deny retrieval and escalate the policy gap.
- When a destructive action is required, identify its exact scope, rollback,
  and required approval before execution.
- When a user-only decision blocks progress, report the decision, available
  options, evidence gathered, and safe work already completed.
- When the selected mode changes, update the execution ledger and required
  completion gates before continuing.

## Communicate the result

Match the final format to the selected mode and keep evidence near each claim.

Start every nontrivial final response with the selected mode and a closed
execution ledger. Then present the mode-specific result below. Omit the ledger
only for a short factual answer that qualified for the execution-control
exception.

For `DESIGN` or `MIGRATE`, include:

1. Outcome, assumptions, and missing evidence.
2. Workload and scale profile.
3. Baseline or the exact plan to create it.
4. Minimum sufficient architecture and rejected alternatives.
5. Data, retrieval, generation, and authorization contracts.
6. Evaluation slices, metrics, and acceptance thresholds.
7. Trace model, dashboards, alerts, and ownership.
8. Latency and cost budgets by stage.
9. Failure states, fallbacks, recovery, and security controls.
10. Vendor boundaries, compatibility, lock-in, and exit path.
11. Delivery, cutover, rollback, risks, and upgrade triggers.

Link the final response to the persistent Markdown plan for `P2` or `P3` work.
Report whether it is proposed, awaiting decisions, approved, in progress,
implemented, or superseded.

A structural validator pass means only that the document shape is valid. Do not
claim the semantic audit is complete until arithmetic is recomputed, current
and target states agree with every diagram, optional components satisfy their
hard gates, and each audit finding is revised, deferred, or accepted explicitly.

For `IMPLEMENT`, report changed files, behavior, verification commands and
results, metric deltas, fallback tests, and remaining risks. For `DEBUG`, report
the symptom, reproduction, evidence trail, root cause, smallest fix, regression
test, and verification. For `AUDIT`, report findings first by severity, then
assumptions, test gaps, and a concise summary. For `OPERATE`, report impact,
mitigation, evidence, current state, recovery actions, and follow-up controls.

Before responding, re-read the request and execution ledger. Verify that every
requirement is completed, deferred with a reason, or blocked by a named missing
decision. Never convert an unverified expectation into a completion claim.
