import unittest

from deadline_service.clock import FakeClock
from deadline_service.service import RagService
from deadline_service.stages import Stage
from deadline_service.tracing import TraceRecorder


class RagServiceTests(unittest.TestCase):
    def make_service(
        self,
        durations: tuple[int, int, int],
    ) -> tuple[RagService, tuple[Stage, Stage, Stage], TraceRecorder]:
        clock = FakeClock()
        stages = (
            Stage("retrieve", durations[0], clock),
            Stage("rerank", durations[1], clock),
            Stage("generate", durations[2], clock),
        )
        tracer = TraceRecorder()
        return RagService(*stages, tracer), stages, tracer

    def test_healthy_path_receives_decreasing_remaining_budgets(self) -> None:
        service, stages, _ = self.make_service((30, 20, 10))

        response = service.answer(100)

        self.assertEqual(response.status, "ok")
        self.assertEqual([stage.timeouts for stage in stages], [[100], [70], [50]])

    def test_stage_exhausting_remaining_budget_stops_downstream_work(self) -> None:
        service, stages, _ = self.make_service((30, 80, 10))

        response = service.answer(100)

        self.assertEqual(response.status, "deadline_exhausted")
        self.assertEqual(stages[1].timeouts, [70])
        self.assertEqual(stages[2].timeouts, [])

    def test_first_stage_timeout_stops_all_downstream_work(self) -> None:
        service, stages, _ = self.make_service((110, 20, 10))

        response = service.answer(100)

        self.assertEqual(response.status, "deadline_exhausted")
        self.assertEqual(stages[1].timeouts, [])
        self.assertEqual(stages[2].timeouts, [])

    def test_deadline_degradation_records_reason(self) -> None:
        service, _, tracer = self.make_service((110, 20, 10))

        service.answer(100)

        self.assertTrue(
            any(
                stage == "request.degraded"
                and attributes["reason"] == "deadline_exhausted"
                for stage, attributes in tracer.events
            )
        )


if __name__ == "__main__":
    unittest.main()
