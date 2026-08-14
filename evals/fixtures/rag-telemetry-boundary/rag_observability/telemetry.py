from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    trace_id: str
    name: str
    attributes: dict[str, object]


@dataclass(frozen=True)
class MetricPoint:
    name: str
    value: float
    attributes: dict[str, str]


@dataclass
class TelemetryRecorder:
    pending: dict[str, list[Span]] = field(default_factory=dict)
    spans: list[Span] = field(default_factory=list)
    metrics: list[MetricPoint] = field(default_factory=list)

    def add_span(
        self,
        trace_id: str,
        name: str,
        **attributes: object,
    ) -> None:
        self.pending.setdefault(trace_id, []).append(
            Span(trace_id, name, attributes)
        )

    def complete(self, trace_id: str, head_sampled: bool, outcome: str) -> None:
        pending = self.pending.pop(trace_id, [])
        if head_sampled:
            self.spans.extend(pending)

    def record_metric(
        self,
        name: str,
        value: float,
        **attributes: str,
    ) -> None:
        self.metrics.append(MetricPoint(name, value, attributes))
