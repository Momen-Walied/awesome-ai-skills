# Evaluation

Use this reference to create repeatable evidence that a RAG change improves the
system. Evaluate retrieval and generation separately, then evaluate the full
user outcome.

## Build the dataset

Start with representative production or domain-expert questions. Add synthetic
questions to improve coverage, but do not let them dominate the acceptance set.

Each case can include:

- query and conversation context;
- tenant, role, time, and other retrieval constraints;
- query class and risk slice;
- relevant document or chunk IDs;
- required facts and acceptable answer variants;
- forbidden claims or sources;
- expected abstention, citation, or tool behavior.

Split development and acceptance cases. Version the dataset and record its
source, ownership, review status, and known blind spots. Prevent test cases from
leaking into prompts, examples, or synthetic source documents.

## Evaluate retrieval

Choose metrics based on available relevance judgments and product behavior.

- Use recall at k to detect missing relevant evidence.
- Use precision at k or context precision to detect noisy evidence.
- Use mean reciprocal rank for a single primary relevant result.
- Use normalized discounted cumulative gain for graded relevance and ranking.
- Measure filter correctness and unauthorized-result rate separately.
- Measure duplicate rate, empty-result rate, and source diversity where useful.

Run `scripts/evaluate_retrieval.py` against JSONL cases that contain
`relevant_ids` and ranked `retrieved_ids`. Compare configurations on identical
cases and query slices.

## Evaluate answers

Keep concepts separate so a high score cannot conceal a dangerous failure.

- Correctness measures whether required facts are present and accurate.
- Faithfulness measures whether claims follow from retrieved evidence.
- Citation correctness measures whether cited passages support their claims.
- Answer relevance measures whether the response addresses the request.
- Completeness measures whether required aspects are covered.
- Abstention accuracy measures whether the system answers only when supported.
- Policy compliance measures access, privacy, and safety behavior.

Use deterministic checks for schemas, citations, identifiers, and required
fields. Use model-based judges for semantic criteria only with a rubric,
calibration set, and periodic human agreement checks.

## Slice every result

Report overall metrics and slices that can fail independently.

Useful slices include query class, language, tenant size, source, document type,
content age, answerability, risk, model, index version, and latency band.

Track confidence intervals or repeated-run variance when model output is
nondeterministic. A small mean improvement with large variance is not a safe
release signal.

### Detect hidden regressions

Compare the baseline and candidate on the same case identifiers, labels, top-k,
and dataset version. Report baseline, candidate, and delta overall and for every
critical cohort. Aggregate improvement cannot compensate for a security
failure or a regression beyond a cohort's declared tolerance. Treat a missing
critical cohort, missing labels, or an empty acceptance slice as an evidence gap,
not a passing zero.

Use paired case-level differences when possible. For small cohorts, publish the
case count and uncertainty or repeated-run variance alongside the mean. Inspect
whether one tenant, language, source, or common query class dominates the
aggregate. Keep unauthorized retrieval, permission-filter correctness,
citation integrity, and other zero-tolerance invariants as independent gates.

For fusion and reranking changes, retain candidate recall before ranking, early
precision after ranking, first-relevant rank, duplicate rate, empty-result rate,
source diversity, latency, and cost. This localizes whether a gain came from
candidate discovery, ordering, or merely increasing fan-out.

## Set release gates

Define absolute thresholds and regression limits before running the candidate.
Require no regression on security and permission tests.

An evaluation gate can require:

- minimum retrieval recall for each critical query class;
- maximum unauthorized retrieval rate of zero;
- minimum citation correctness and faithfulness;
- bounded quality regression for noncritical slices;
- p95 latency and cost within budget;
- successful failure and fallback tests.

Keep the current production configuration as the baseline. Store configuration,
code, prompt, model, embedding, index, and dataset versions with every run.

### Guide an evaluation implementation

Locate the repository's existing datasets, scorers, experiment tracking, and
release command before adding an evaluator. Preserve the current system as the
baseline, freeze dataset and configuration versions, and change one meaningful
variable per comparison. Add the smallest missing slice or metric that can
falsify the proposed improvement.

Guide the host to use framework-native evaluators when their contracts remain
inspectable, and deterministic local checks for identifiers, authorization,
schema, and citations. Do not replace a working harness to standardize on a
preferred evaluation vendor. Report missing labels or judge calibration as
evidence gaps rather than manufacturing scores.

## Evaluate in production

Use shadow traffic, canaries, or controlled experiments after offline gates
pass. Monitor answer success, abstention, reformulation, escalation, user
correction, latency, errors, and cost.

Treat implicit feedback carefully because clicks and session length can reward
confusing answers. Sample production failures for expert labeling and add them
to the regression set after removing sensitive information.

## Primary references

- Thakur et al., [BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of
  Information Retrieval Models](https://arxiv.org/abs/2104.08663), which shows
  why retrieval methods need evaluation across heterogeneous tasks instead of
  one aggregate or in-domain result.
