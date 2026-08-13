from fallback_service.models import Chunk, IndexView
from fallback_service.retrievers import PrimaryRetriever
from fallback_service.tracing import TraceRecorder


class RetrievalService:
    def __init__(
        self,
        primary: PrimaryRetriever,
        fallback: IndexView,
        tracer: TraceRecorder,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._tracer = tracer

    def search(
        self,
        tenant_id: str,
        required_policy_sequence: int,
    ) -> list[Chunk]:
        try:
            results = self._primary.search(tenant_id)
            self._tracer.record("retrieve.primary", result_count=len(results))
            return results
        except TimeoutError:
            results = [
                chunk
                for chunk in self._fallback.chunks
                if chunk.tenant_id == tenant_id
            ]
            self._tracer.record(
                "fallback.selected",
                reason="primary_timeout",
                fallback_policy_sequence=self._fallback.policy_sequence,
                required_policy_sequence=required_policy_sequence,
            )
            return results
