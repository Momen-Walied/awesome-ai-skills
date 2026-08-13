# Agent and skill interoperability

Use this reference to operate across coding agents without coupling the RAG
workflow to one model, command syntax, or orchestration plugin.

## Discover the host

At the start of nontrivial work, inspect the environment for capabilities rather
than product names:

- repository instructions such as `AGENTS.md`, `CLAUDE.md`, and nested rules;
- existing specifications and plans such as `.specify/`, `specs/`, OpenSpec,
  or repository-native design records;
- available skills and their declared scope;
- native task tracking, subagents, hooks, MCP servers, connectors, browsers,
  code execution, and approval boundaries;
- project commands for tests, linting, evaluation, development, and deployment.

Use the host's native mechanism when available. If it is absent, use a simple
Markdown ledger and direct tools. Never pretend an unavailable tool, skill,
hook, or subagent exists.

## Compose instead of competing

This skill owns RAG domain reasoning: retrieval and ingestion contracts,
evaluation, authorization, observability, reliability, scale, and migration.
Let other capabilities retain their natural ownership:

- Spec Kit or another spec workflow owns its specification, clarification,
  task, and implementation artifacts.
- Repository instruction files own local conventions and verification commands.
- Cloud, database, security, browser, document, and deployment skills own their
  specialized operations.
- The host orchestrator owns model selection, delegation, continuation, hooks,
  and task persistence.

The host agent remains the executor. Do not simulate tools, prescribe hidden
reasoning, or claim that this skill performed a repository action. Guide the
host toward observable operations and let it choose equivalent native tools.
Bundled scripts support deterministic inspection or calculation; they do not
replace repository code, provider SDKs, or specialist skills.

Read and extend the existing artifact. Do not create `docs/plans/...` when the
repository already has an active spec workflow unless that workflow calls for
it. Do not duplicate a todo list maintained by the host.

When instructions conflict, follow the host's precedence rules and the user's
latest intent. Preserve hard security and evidence boundaries, then report any
remaining conflict briefly.

## Use tools by capability

Describe required operations semantically so different agents can map them to
their native tools:

- search symbols and call sites;
- read files and repository instructions;
- inspect history and working-tree state;
- run focused and broad verification;
- query documentation or live systems when authorized;
- delegate independent, read-only investigation when it reduces latency;
- request approval for destructive, privileged, or external writes.

Parallelize independent reads and measurements. Serialize edits that touch the
same contract. Give delegated work one objective, expected evidence, relevant
paths, constraints, and a return format. Verify delegated conclusions against
the repository before editing.

## Keep the workflow model-neutral

Use observable artifacts instead of hidden reasoning requirements. Ask for a
system map, scenario contracts, code diff, test output, trace, benchmark, or
decision record. Avoid depending on chain-of-thought wording, exact progress
phrases, or a specific tool-call transcript.

Keep core instructions concise and load domain references only when the task
needs them. This supports hosts that advertise metadata first and load skill
bodies or resources on demand.

## Integrate with common harnesses

- With Spec Kit, detect its files and continue the active phase. Feed RAG
  scenarios and nonfunctional gates into the existing spec and task artifacts.
- With OpenCode or oh-my-openagent, use available skills, categories, MCPs, and
  subagents through the host interface. Do not require plugin-specific agents.
- With Claude Code, respect project and nested instructions, tool permissions,
  and skill progressive disclosure.
- With Codex, respect `AGENTS.md`, sandbox and approval policy, native plans,
  installed skills, and MCP or app connectors.
- With an unknown agent, fall back to portable `SKILL.md` instructions,
  repository files, shell commands, and a compact Markdown ledger.

The portable outcome is consistent engineering behavior, not identical console
text across hosts.
