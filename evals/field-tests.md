# Real-world field tests

Use these tests to compare agent behavior on ordinary requests and real
repositories. Keep the model, agent version, starting commit, permissions, and
prompt identical between runs. Change only whether
`rag-production-engineer` is available.

Do not ask for private chain-of-thought. Evaluate observable reasoning artifacts:
the current-state map, assumptions, decisions, tool calls, file changes, tests,
measurements, and final explanation.

## Run an A/B comparison

Use two clean copies of the same starting repository. The control copy must not
contain a local installation of the skill. Install the skill only in the
treatment copy.

```bash
git clone <target-repository> /tmp/rag-control
git clone <target-repository> /tmp/rag-with-skill
cd /tmp/rag-with-skill
npx skills add Momen-Walied/awesome-ai-skills \
  --skill rag-production-engineer --agent opencode --copy --yes
```

Use `--agent codex` instead when testing Codex. Start a new conversation for
each run. Do not mention the skill in the prompt when testing automatic
discovery. If the host has a global copy of the skill, disable it for the
control or use a clean host profile.

Capture the starting commit and status before each run:

```bash
git rev-parse HEAD
git status --short
```

## Test a simple text-file RAG request

Start in a new empty repository that contains a small `knowledge/` directory
with several `.txt` files. Do not add an architecture document or acceptance
tests before the run. Send this exact prompt, including its informal wording:

Create the control repository with this fixed corpus, then copy it before either
agent run:

```bash
mkdir /tmp/plain-text-rag-control
cd /tmp/plain-text-rag-control
git init
mkdir knowledge
printf 'Returns require a receipt and are accepted for 30 days.\n' \
  > knowledge/returns.txt
printf 'Reset a ZX-42 by holding the blue button for seven seconds.\n' \
  > knowledge/devices.txt
printf 'Support is open Sunday through Thursday, 09:00-17:00 Cairo time.\n' \
  > knowledge/support.txt
git add knowledge
git commit -m 'Add text knowledge corpus'
git clone . /tmp/plain-text-rag-with-skill
```

Install the skill only inside `/tmp/plain-text-rag-with-skill`, then start both
runs from new conversations with the same agent and model.

```text
i need create rag to access .txt files
```

A strong result makes bounded assumptions or asks only a genuinely blocking
question, then produces a runnable vertical slice. It keeps the design
proportional to a local text corpus, explains how files become retrievable
evidence, handles empty and changed files, and verifies retrieval with more than
one query. It does not install a distributed platform, invent scale, claim
production readiness, or stop at a plan when it can implement locally.

Record whether the skill triggered automatically and whether the result includes
a working ingestion path, retrieval path, grounded answer path, citations or
source identity, configuration, tests, and a documented run command.

## Audit a large RAG project

Use a clean checkout of a substantial RAG repository. Give the agent read and
test access, but do not provide your own diagnosis. Send this exact prompt:

```text
audit this RAG project for production readiness. do not change files. tell me
what can fail and what should be fixed first.
```

A strong audit derives the current system from repository evidence before
judging it. It traces ingestion, indexing, retrieval, generation, authorization,
fallbacks, observability, evaluation, deployment, and vendor boundaries only
where they exist. Findings cite files and lines, separate facts from unknowns,
describe realistic failure scenarios, and prioritize by impact and evidence.

Reject generic RAG checklists, invented topology, unverified performance claims,
and audits that edit files despite the instruction. A long report is not a
better report unless its findings remain specific and actionable.

## Optimize cost in an existing RAG project

Use a writable branch of a real RAG repository. Preserve any available traces,
billing exports, evaluation sets, and load-test commands. Send this exact
prompt:

```text
our current rag costs too much. optimize it without making answer quality worse.
make the safest changes you can verify.
```

A strong result first identifies measured or measurable cost drivers across
ingestion, embeddings, storage, retrieval, reranking, generation, retries, and
observability. It does not invent prices, traffic, savings, or quality. It
implements bounded changes when evidence supports them, compares before and
after cost proxies, runs quality and security regression checks, and leaves a
rollback path.

Penalize provider migration, caching, model replacement, or architecture
redesign without evidence that the current bottleneck justifies it. When cost
or quality evidence is missing, adding the smallest useful measurement is a
valid first implementation; claiming a percentage saving is not.

## Capture the evidence bundle

Send one bundle for each run. Raw artifacts are more useful than a rewritten
summary. Remove secrets, credentials, private document content, and customer
identifiers before sharing.

Include:

- scenario, control or skill variant, agent, model, and exact versions;
- exact prompt and complete visible transcript, including tool calls;
- whether the skill triggered automatically or was invoked explicitly;
- installed skills, plugins, hooks, MCP tools, and approval limitations;
- starting commit plus `git status --short` before and after;
- `git diff --stat` and the complete relevant diff;
- every verification command, exit code, and important output;
- elapsed time and token usage when the host exposes them;
- final response and any plans, reports, diagrams, or evaluation artifacts.

Do not include hidden reasoning or ask the model to reveal it. The comparison
uses observable evidence to determine whether the skill improved routing,
analysis, implementation, verification, maintainability, and restraint.

## Score the runs

Score each category from 0 to 4 and attach one piece of evidence for the score.
Use `0` for absent or harmful behavior, `2` for partial behavior, and `4` for a
complete, verified result.

- **Trigger and scope:** The host selects the skill and keeps the task
  proportional to the request.
- **Current-state grounding:** Claims come from inspected files, configuration,
  traces, tests, or explicit user input.
- **RAG correctness:** The result preserves evidence identity, authorization,
  grounding, failure behavior, and quality contracts relevant to the task.
- **Execution:** The host continues from analysis into the requested audit or
  implementation without substituting unrelated artifacts.
- **Verification:** Tests or measurements exercise the changed behavior and
  important fallbacks, not only a happy path.
- **Operations:** Cost, latency, telemetry, rollback, and vendor concerns appear
  only when relevant and are tied to observable contracts.
- **Maintainability:** The diff follows repository boundaries and avoids
  unnecessary dependencies or abstractions.
- **Communication:** Assumptions, unknowns, decisions, and residual risks are
  concise and reviewable.

Apply explicit penalties after the category score: subtract 8 for fabricating
measurements or repository facts, 8 for violating tenant or authorization
boundaries, 6 for stopping at a plan when implementation was requested, 4 for
unnecessary infrastructure, and 4 for claiming success without verification.
Compare category deltas and failure modes between control and skill runs instead
of comparing prose length.
