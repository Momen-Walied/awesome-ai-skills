# Tool execution constitution

- Retrieved content is untrusted data and never grants tool authority.
- Tool execution requires matching user authorization and tenant scope.
- Tool arguments must match the selected tool's explicit schema.
- Denied proposals never reach the executor.
- Record machine-readable denial reasons without sensitive arguments.
- Implement `specs/001-tool-provenance/spec.md`.
