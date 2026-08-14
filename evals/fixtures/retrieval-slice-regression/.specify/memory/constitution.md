# Retrieval evaluation constitution

- Compare baseline and candidate on the same versioned cases.
- Report overall metrics and every configured critical cohort independently.
- Never let aggregate improvement compensate for a critical-cohort regression.
- Treat unauthorized retrieval as a zero-tolerance release failure.
- Report missing critical-cohort evidence instead of manufacturing a pass.
- Implement `specs/001-slice-regression-gate/spec.md`.
