# Incremental ingestion constitution

- Preserve the source sequence through index mutation and checkpoint commit.
- Make replay idempotent after restart or duplicate delivery.
- Remove deleted or revoked documents from searchable state.
- Reject unsupported source events without advancing the checkpoint.
- Record mutation outcomes without logging document content.
- Implement the scenarios in `specs/001-incremental-revocation/spec.md`.
