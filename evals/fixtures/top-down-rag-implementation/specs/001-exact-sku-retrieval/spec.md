# Exact SKU retrieval

## User scenario

When an authorized user searches for an exact SKU such as `ZX-42`, the product
page must rank before a semantically related family manual.

## Acceptance scenarios

1. With exact-match retrieval enabled, `ZX-42` returns the authorized product
   page first and records the selected retrieval strategy.
2. A tenant can never receive another tenant's exact SKU page.
3. With exact-match retrieval disabled, the existing dense route remains the
   behavior and rollback path.
