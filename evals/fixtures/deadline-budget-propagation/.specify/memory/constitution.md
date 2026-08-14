# Request deadline constitution

- Use one end-to-end monotonic request budget.
- Derive each stage timeout from the remaining budget.
- Stop downstream work after deadline exhaustion.
- Preserve the healthy answer path and record degradation reasons.
- Implement `specs/001-deadline-propagation/spec.md`.
