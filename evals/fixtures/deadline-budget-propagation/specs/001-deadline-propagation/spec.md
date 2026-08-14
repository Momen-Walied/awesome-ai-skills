# Deadline propagation

## User scenario

A RAG request with a 100 millisecond budget must not give each sequential stage
a fresh 100 millisecond timeout.

## Acceptance scenarios

1. Healthy stages receive decreasing remaining budgets and return the answer.
2. A stage that cannot finish within the remaining budget degrades the request
   and prevents later stages from starting.
3. An exhausted first stage also prevents all downstream calls.
4. Deadline degradation records a machine-readable reason.
