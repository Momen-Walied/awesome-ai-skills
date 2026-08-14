# Hybrid rank fusion

## User scenario

Dense and lexical retrieval return complementary evidence with incompatible raw
score scales. The current fusion lets the lexical scale dominate and returns a
duplicate document when the same evidence appears in both lists.

## Acceptance scenarios

1. A document supported by both rankings is first after fusion without comparing
   raw dense and lexical scores.
2. A stable document identifier appears at most once before the final limit.
3. Tenant authorization is applied before dense retrieval, lexical retrieval,
   and fusion.
4. Disabling hybrid retrieval preserves the existing dense-only rollback route.
5. Traces identify the route and bounded candidate counts without query text,
   document content, or raw scores.
