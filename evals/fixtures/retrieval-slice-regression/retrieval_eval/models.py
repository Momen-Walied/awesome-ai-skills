from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievalCase:
    case_id: str
    cohort: str
    relevant_ids: frozenset[str]
    baseline_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    forbidden_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class CohortMetrics:
    baseline_recall: float
    candidate_recall: float
    delta: float


@dataclass(frozen=True)
class GateResult:
    passed: bool
    overall_baseline_recall: float
    overall_candidate_recall: float
    cohort_metrics: dict[str, CohortMetrics]
    reasons: tuple[str, ...]
    dataset_version: str
    baseline_version: str
    candidate_version: str
