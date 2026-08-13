# Evaluation strategy

Evaluate the skill as a portable engineering workflow, not as a prompt that
must produce identical prose from every model.

## Evaluation layers

Use four complementary layers:

1. **Discovery:** Does the host expose and invoke the skill for substantive RAG
   work while avoiding unrelated tasks?
2. **Reasoning artifacts:** Does the agent build a grounded current-state map,
   select relevant scenarios, and explain decisions with repository evidence?
3. **Implementation:** Does the agent modify the correct ownership boundary and
   pass executable acceptance, regression, security, and rollback tests?
4. **Interoperability:** Does the skill coexist with repository instructions,
   active spec workflows, other skills, native task state, tools, and approval
   policies?

Keyword checks in `cases.jsonl` provide inexpensive smoke signals. They are not
proof of engineering quality. Workspace fixtures and their verification
commands are the primary evidence for implementation cases.

## Avoid benchmark overfitting

Do not add a core instruction for every failed transcript. Promote a finding
into the skill only when at least one condition holds:

- it is a domain safety invariant, such as tenant isolation or revocation
  freshness;
- it recurs across multiple models or agent harnesses;
- it exposes a missing general workflow step;
- it can be expressed as an observable contract without prescribing one
  implementation.

Keep model-specific wording and tool syntax out of the core skill. Prefer
capability detection, repository artifacts, scenario outcomes, tests, traces,
and measurable gates. Maintain held-out prompts and rotate domain details so a
skill cannot pass by memorizing fixture nouns.

## Cross-agent matrix

Run representative cases on Codex, Claude Code, OpenCode, and Antigravity when
release scope permits. Add other harnesses without changing the case's outcome
contract.

For each host, record:

- model and agent version;
- installed skills, plugins, hooks, and MCPs;
- whether the skill triggered automatically or was explicitly invoked;
- tool and approval limitations;
- produced artifacts and repository diff;
- verification commands and exit codes;
- elapsed time and token usage when available;
- human review notes for maintainability and unnecessary complexity.

Compare distributions and failure clusters, not one best-looking response. A
release can retain known model-specific failures when they are documented and
the fix would overfit or weaken another host.

Store reviewed release matrices in `records/`. Keep transcripts outside the
repository unless a short excerpt is necessary to explain a failure.

## Implementation cases

`top-down-rag-implementation` is the first end-to-end implementation case. It
contains an existing Spec Kit artifact, a layered retrieval service, telemetry,
tenant policy, a rollback flag, and one failing acceptance scenario. The agent
must make the suite pass through a bounded implementation rather than producing
a parallel plan.

Add future implementation fixtures across ingestion replay, retrieval quality,
authorization, tracing, latency, and provider failure. Keep each fixture small
enough to inspect, but include enough layers to require real system tracing.
