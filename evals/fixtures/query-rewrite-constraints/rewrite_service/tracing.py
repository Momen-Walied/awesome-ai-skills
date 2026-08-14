from dataclasses import dataclass, field


@dataclass
class TraceRecorder:
    events: list[tuple[str, dict[str, object]]] = field(default_factory=list)

    def record(self, stage: str, **attributes: object) -> None:
        self.events.append((stage, attributes))
