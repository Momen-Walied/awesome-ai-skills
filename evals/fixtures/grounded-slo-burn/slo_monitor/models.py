from dataclasses import dataclass


@dataclass(frozen=True)
class RequestOutcome:
    http_status: int
    grounded: bool
    latency_ms: int


@dataclass(frozen=True)
class Window:
    outcomes: tuple[RequestOutcome, ...]


@dataclass(frozen=True)
class Alert:
    firing: bool
    reason: str | None = None
    owner: str | None = None
    runbook: str | None = None
