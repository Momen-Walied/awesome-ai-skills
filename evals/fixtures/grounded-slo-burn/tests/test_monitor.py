import unittest

from slo_monitor.models import RequestOutcome, Window
from slo_monitor.monitor import GroundedSloMonitor


GOOD = RequestOutcome(200, True, 200)
UNGROUNDED = RequestOutcome(200, False, 200)
SLOW = RequestOutcome(200, True, 1500)


def window(*, total: int, bad: int = 0, bad_outcome: RequestOutcome = UNGROUNDED) -> Window:
    return Window((bad_outcome,) * bad + (GOOD,) * (total - bad))


class GroundedSloMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.monitor = GroundedSloMonitor()

    def test_ungrounded_http_success_counts_as_bad(self) -> None:
        burn = self.monitor.burn_rate(window(total=100, bad=10))

        self.assertAlmostEqual(burn, 10.0)

    def test_slow_grounded_answer_counts_as_bad(self) -> None:
        burn = self.monitor.burn_rate(
            window(total=100, bad=10, bad_outcome=SLOW)
        )

        self.assertAlmostEqual(burn, 10.0)

    def test_short_spike_without_long_burn_does_not_page(self) -> None:
        alert = self.monitor.evaluate(
            window(total=100, bad=20),
            window(total=1000, bad=10),
        )

        self.assertFalse(alert.firing)

    def test_sustained_fast_burn_has_owner_and_runbook(self) -> None:
        alert = self.monitor.evaluate(
            window(total=100, bad=20),
            window(total=1000, bad=100),
        )

        self.assertTrue(alert.firing)
        self.assertEqual(alert.reason, "grounded_slo_fast_burn")
        self.assertEqual(alert.owner, "rag-oncall")
        self.assertEqual(alert.runbook, "runbooks/grounded-slo.md")

    def test_no_traffic_has_zero_burn_and_no_alert(self) -> None:
        empty = Window(())

        self.assertEqual(self.monitor.burn_rate(empty), 0.0)
        self.assertFalse(self.monitor.evaluate(empty, empty).firing)


if __name__ == "__main__":
    unittest.main()
