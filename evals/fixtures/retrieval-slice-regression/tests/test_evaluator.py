import unittest

from retrieval_eval.evaluator import RetrievalReleaseGate
from retrieval_eval.models import RetrievalCase


def case(
    case_id: str,
    cohort: str,
    *,
    baseline_hit: bool,
    candidate_hit: bool,
    forbidden_candidate: bool = False,
) -> RetrievalCase:
    relevant_id = f"relevant-{case_id}"
    candidate_ids = (relevant_id,) if candidate_hit else (f"noise-{case_id}",)
    forbidden_ids: frozenset[str] = frozenset()
    if forbidden_candidate:
        candidate_ids += (f"private-{case_id}",)
        forbidden_ids = frozenset({f"private-{case_id}"})
    return RetrievalCase(
        case_id,
        cohort,
        frozenset({relevant_id}),
        (relevant_id,) if baseline_hit else (f"old-noise-{case_id}",),
        candidate_ids,
        forbidden_ids,
    )


def regression_cases() -> list[RetrievalCase]:
    common = [
        case(
            f"common-{index}",
            "common",
            baseline_hit=index < 4,
            candidate_hit=True,
        )
        for index in range(8)
    ]
    rare = [
        case(
            f"rare-{index}",
            "rare-language",
            baseline_hit=True,
            candidate_hit=False,
        )
        for index in range(2)
    ]
    return common + rare


class RetrievalReleaseGateTests(unittest.TestCase):
    def make_gate(self) -> RetrievalReleaseGate:
        return RetrievalReleaseGate(critical_cohorts=frozenset({"rare-language"}))

    def evaluate(self, cases: list[RetrievalCase]):
        return self.make_gate().evaluate(
            cases,
            dataset_version="dataset-2026-08-14",
            baseline_version="retriever-a",
            candidate_version="retriever-b",
        )

    def test_overall_candidate_improvement_is_preserved(self) -> None:
        result = self.evaluate(regression_cases())

        self.assertAlmostEqual(result.overall_baseline_recall, 0.6)
        self.assertAlmostEqual(result.overall_candidate_recall, 0.8)

    def test_critical_cohort_regression_blocks_aggregate_improvement(self) -> None:
        result = self.evaluate(regression_cases())

        self.assertFalse(result.passed)
        self.assertIn("critical_cohort_regression:rare-language", result.reasons)

    def test_report_includes_every_observed_cohort_metric(self) -> None:
        result = self.evaluate(regression_cases())

        self.assertEqual(set(result.cohort_metrics), {"common", "rare-language"})
        common = result.cohort_metrics["common"]
        rare = result.cohort_metrics["rare-language"]
        self.assertAlmostEqual(common.baseline_recall, 0.5)
        self.assertAlmostEqual(common.candidate_recall, 1.0)
        self.assertAlmostEqual(common.delta, 0.5)
        self.assertAlmostEqual(rare.baseline_recall, 1.0)
        self.assertAlmostEqual(rare.candidate_recall, 0.0)
        self.assertAlmostEqual(rare.delta, -1.0)

    def test_unauthorized_candidate_result_always_blocks_release(self) -> None:
        unsafe = case(
            "unsafe",
            "rare-language",
            baseline_hit=True,
            candidate_hit=True,
            forbidden_candidate=True,
        )

        result = self.evaluate([unsafe])

        self.assertFalse(result.passed)
        self.assertIn("unauthorized_candidate_result", result.reasons)

    def test_unauthorized_candidate_outside_quality_top_k_still_blocks(self) -> None:
        unsafe = RetrievalCase(
            "unsafe-tail",
            "rare-language",
            frozenset({"relevant"}),
            ("relevant",),
            ("relevant", "noise-1", "noise-2", "private"),
            frozenset({"private"}),
        )

        result = self.evaluate([unsafe])

        self.assertFalse(result.passed)
        self.assertIn("unauthorized_candidate_result", result.reasons)

    def test_missing_critical_cohort_is_an_evidence_gap(self) -> None:
        only_common = [
            case("common-only", "common", baseline_hit=True, candidate_hit=True)
        ]

        result = self.evaluate(only_common)

        self.assertFalse(result.passed)
        self.assertIn("missing_critical_cohort:rare-language", result.reasons)

    def test_result_preserves_all_evaluation_versions(self) -> None:
        result = self.evaluate(regression_cases())

        self.assertEqual(result.dataset_version, "dataset-2026-08-14")
        self.assertEqual(result.baseline_version, "retriever-a")
        self.assertEqual(result.candidate_version, "retriever-b")


if __name__ == "__main__":
    unittest.main()
