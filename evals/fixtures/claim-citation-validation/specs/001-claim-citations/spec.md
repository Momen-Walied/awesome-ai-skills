# Claim-level citation validation

## User scenario

A generated answer must not pass validation by citing a real context chunk that
does not support the claim.

## Acceptance scenarios

1. A claim citing a supplied chunk with its supporting fact remains an answer.
2. A claim citing a valid but unrelated chunk causes abstention.
3. A material claim without a citation causes abstention.
4. A citation outside the supplied context causes abstention.
5. Every validation result records whether the answer was grounded.
6. Validation traces contain no raw claim text or evidence content.
