# RAG execution protocol

Use this protocol when the user asks to implement, fix, optimize, migrate, or
operate an existing RAG system. Planning is a control surface for risky work,
not the deliverable when working code was requested.

## Build a top-down system model

Start at the user-visible entry point and trace both runtime directions before
editing code:

1. Map repository boundaries, deployable services, entry points, configuration,
   tests, and existing specifications.
2. Trace the query path from API to policy resolution, retrieval, ranking,
   context assembly, generation, validation, and response.
3. Trace the data path from source discovery through parsing, chunking,
   embedding, indexing, updates, deletes, and permission revocations.
4. Locate control-plane behavior: flags, provider selection, index versions,
   prompts, quotas, deadlines, retries, fallbacks, and rollout state.
5. Locate evidence: tests, evaluation datasets, traces, dashboards, runbooks,
   incidents, and known-good baselines.

Record observations separately from inferences. Follow concrete symbols and
call sites instead of guessing architecture from directory names. For a bounded
change, stop when the affected path and public contract are understood. For a
cross-component change, persist the map in the project's existing spec or plan
artifact.

## Derive scenarios from contracts

Create only the scenarios that can falsify the requested behavior. Start with
the current happy path, then select relevant variants:

- authorized answer with sufficient evidence;
- exact identifier or keyword query;
- empty, low-confidence, conflicting, or stale evidence;
- cross-tenant access and permission revocation;
- document update, delete, replay, and partial indexing;
- provider timeout, rate limit, malformed response, and recovery;
- high load, hot tenant, queue backlog, and deadline exhaustion;
- fallback, rollback, restart, and version skew.

Turn each selected scenario into an observable contract: input, initial state,
expected result, forbidden result, and evidence source. Prefer tests at stable
boundaries over assertions about internal implementation details.

## Implement a vertical slice

When implementation is requested and no genuine blocker remains, continue into
code in the same task:

1. Reproduce the failure or record the baseline.
2. Identify the smallest ownership boundary that can fix it.
3. Reuse repository interfaces, configuration, dependency injection, and test
   style.
4. Change one coherent path from input to observable output.
5. Add or update a regression test that fails before the change.
6. Add telemetry for a changed stage when the system already has telemetry.
7. Run focused verification, then the relevant broader suite.
8. Exercise the rollback or failure path when the blast radius warrants it.

Do not stop after producing a plan when the user requested implementation.
Do not create a broad framework when a local change passes the scenarios. Do
not replace an existing architecture with a reference architecture merely
because it is cleaner in isolation.

## Re-plan from evidence

Treat plans and specifications as living coordination artifacts. Update the
existing artifact when implementation reveals a wrong assumption, changed
interface, new dependency, or failed gate. Preserve the reason for the change.
Do not maintain a second competing plan.

## Verify outcomes

Completion requires evidence at the same boundary as the request:

- behavior change: focused test plus relevant regression suite;
- retrieval change: slice metrics against the recorded baseline;
- ingestion change: replay, idempotency, delete, and freshness evidence;
- security change: adversarial tenant and revocation tests;
- reliability change: injected failure and recovery evidence;
- performance change: stage and end-to-end percentiles under a stated load;
- migration change: convergence, canary, rollback, and retirement gates.

Report what ran, what changed, and what remains unverified. A plan validator,
lint command, or keyword match cannot substitute for runtime evidence.
