# Incremental revocation

## User scenario

When a source revokes access to a previously indexed document, incremental
ingestion must remove it before advancing the durable checkpoint.

## Acceptance scenarios

1. An upsert followed by a revocation leaves no searchable document and records
   a revocation outcome.
2. A hard-delete event also removes the document.
3. Replaying an already committed event range performs no additional index
   mutations.
4. A successful later upsert can index a new authorized source version.
5. An unsupported event fails without advancing the checkpoint.
