# Retrieval slice regression gate

## User scenario

A candidate retriever improves aggregate recall but loses every relevant result
for a critical rare-language cohort. The current release gate compares only the
aggregate, so it approves the unsafe candidate.

## Acceptance scenarios

1. Baseline and candidate recall are computed from the same cases and top-k.
2. The report includes a baseline, candidate, and delta for every observed
   cohort.
3. Any regression beyond the configured limit in a critical cohort blocks the
   release even when aggregate recall improves.
4. Any unauthorized candidate result blocks the release independently of
   retrieval quality.
5. A configured critical cohort with no cases is reported as missing evidence
   and cannot pass.
6. Dataset, baseline, and candidate versions remain attached to the result.
