from slo_monitor.models import Alert, Window


class GroundedSloMonitor:
    def __init__(
        self,
        *,
        target: float = 0.99,
        latency_budget_ms: int = 1000,
        short_burn_threshold: float = 14.0,
        long_burn_threshold: float = 6.0,
    ) -> None:
        self._target = target
        self._latency_budget_ms = latency_budget_ms
        self._short_burn_threshold = short_burn_threshold
        self._long_burn_threshold = long_burn_threshold

    def burn_rate(self, window: Window) -> float:
        if not window.outcomes:
            return 0.0
        good = sum(
            outcome.http_status < 500
            for outcome in window.outcomes
        )
        bad_ratio = 1 - (good / len(window.outcomes))
        return bad_ratio / (1 - self._target)

    def evaluate(self, short: Window, long: Window) -> Alert:
        short_burn = self.burn_rate(short)
        if short_burn >= self._short_burn_threshold:
            return Alert(True, reason="grounded_slo_fast_burn")
        return Alert(False)
