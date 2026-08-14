from collections.abc import Iterable

from retrieval_eval.models import GateResult, RetrievalCase


def _recall(cases: Iterable[RetrievalCase], field: str, top_k: int) -> float:
    selected = list(cases)
    if not selected:
        return 0.0
    hits = sum(
        bool(case.relevant_ids.intersection(getattr(case, field)[:top_k]))
        for case in selected
    )
    return hits / len(selected)


class RetrievalReleaseGate:
    def __init__(
        self,
        *,
        critical_cohorts: frozenset[str],
        top_k: int = 3,
        max_critical_regression: float = 0.0,
    ) -> None:
        self._critical_cohorts = critical_cohorts
        self._top_k = top_k
        self._max_critical_regression = max_critical_regression

    def evaluate(
        self,
        cases: list[RetrievalCase],
        *,
        dataset_version: str,
        baseline_version: str,
        candidate_version: str,
    ) -> GateResult:
        """Current gate incorrectly assumes aggregate improvement is sufficient."""
        del self._critical_cohorts, self._max_critical_regression
        baseline = _recall(cases, "baseline_ids", self._top_k)
        candidate = _recall(cases, "candidate_ids", self._top_k)
        return GateResult(
            passed=candidate >= baseline,
            overall_baseline_recall=baseline,
            overall_candidate_recall=candidate,
            cohort_metrics={},
            reasons=(),
            dataset_version=dataset_version,
            baseline_version=baseline_version,
            candidate_version=candidate_version,
        )
