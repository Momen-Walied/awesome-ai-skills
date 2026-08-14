# Retrieved-content tool provenance

## User scenario

A retrieved document containing instructions to call a tool must not cause that
tool to execute, including when the tool itself is allowlisted.

## Acceptance scenarios

1. A user-originated, authorized, tenant-scoped read call executes.
2. An allowlisted tool proposed by retrieved content is denied and traced.
3. A user-originated call targeting another tenant is denied and traced.
4. A non-allowlisted tool is denied.
5. No denied proposal reaches the executor.
6. Unknown or smuggled arguments are denied before execution.
