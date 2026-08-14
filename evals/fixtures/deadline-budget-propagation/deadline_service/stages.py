from deadline_service.clock import FakeClock


class Stage:
    def __init__(self, name: str, duration_ms: int, clock: FakeClock) -> None:
        self.name = name
        self.duration_ms = duration_ms
        self.clock = clock
        self.timeouts: list[int] = []

    def run(self, timeout_ms: int) -> str:
        self.timeouts.append(timeout_ms)
        if self.duration_ms > timeout_ms:
            self.clock.advance(timeout_ms)
            raise TimeoutError(f"{self.name} exceeded its timeout")
        self.clock.advance(self.duration_ms)
        return self.name
