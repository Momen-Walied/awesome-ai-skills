from rag_service.config import RetrievalSettings
from rag_service.models import Chunk
from rag_service.policy import authorized_chunks
from rag_service.retrieval import DenseRetriever
from rag_service.tracing import TraceRecorder


class RetrievalService:
    def __init__(
        self,
        chunks: list[Chunk],
        settings: RetrievalSettings,
        tracer: TraceRecorder,
    ) -> None:
        self._chunks = chunks
        self._settings = settings
        self._tracer = tracer
        self._dense = DenseRetriever()

    def search(self, tenant_id: str, query: str) -> list[Chunk]:
        candidates = authorized_chunks(self._chunks, tenant_id)
        self._tracer.record(
            "policy.resolve", tenant_id=tenant_id, candidate_count=len(candidates)
        )
        results = self._dense.search(query, candidates)
        self._tracer.record("retrieve.dense", result_count=len(results))
        return results
