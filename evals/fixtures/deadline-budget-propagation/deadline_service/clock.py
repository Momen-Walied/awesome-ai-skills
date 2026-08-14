from dataclasses import dataclass


@dataclass
class FakeClock:
    now_ms: int = 0

    def advance(self, duration_ms: int) -> None:
        self.now_ms += duration_ms
