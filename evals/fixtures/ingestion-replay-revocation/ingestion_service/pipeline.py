from collections.abc import Iterable

from ingestion_service.checkpoint import Checkpoint
from ingestion_service.index import SearchIndex
from ingestion_service.models import SourceEvent
from ingestion_service.tracing import TraceRecorder


class IngestionPipeline:
    def __init__(
        self,
        index: SearchIndex,
        checkpoint: Checkpoint,
        tracer: TraceRecorder,
    ) -> None:
        self._index = index
        self._checkpoint = checkpoint
        self._tracer = tracer

    def apply(self, events: Iterable[SourceEvent]) -> None:
        for event in events:
            if event.sequence <= self._checkpoint.sequence:
                continue
            if event.kind == "upsert":
                self._index.upsert(event)
            self._checkpoint.sequence = event.sequence
            self._tracer.record(
                "ingest.apply",
                sequence=event.sequence,
                kind=event.kind,
                outcome="indexed",
            )
