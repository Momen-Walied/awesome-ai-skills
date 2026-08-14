from rerank_service.config import RerankSettings
from rerank_service.dependencies import Reranker, Retriever
from rerank_service.models import Candidate
from rerank_service.tracing import TraceRecorder


class RetrievalService:
    def __init__(
        self,
        settings: RerankSettings,
        retriever: Retriever,
        reranker: Reranker,
        tracer: TraceRecorder,
    ) -> None:
        self._settings = settings
        self._retriever = retriever
        self._reranker = reranker
        self._tracer = tracer

    def search(self, tenant_id: str, query: str) -> list[Candidate]:
        candidates = self._retriever.search(tenant_id, query)
        if not self._settings.enable_reranker:
            self._tracer.record("retrieve.original", result_count=len(candidates))
            return candidates

        window = candidates[: self._settings.window]
        try:
            output_ids = self._reranker.rerank(
                query,
                window,
                self._settings.timeout_ms,
            )
        except TimeoutError:
            self._tracer.record("rerank.fallback", reason="timeout")
            return []

        by_id = {candidate.document_id: candidate for candidate in window}
        results = [by_id[document_id] for document_id in output_ids if document_id in by_id]
        self._tracer.record(
            "rerank.selected",
            input_count=len(window),
            output_count=len(results),
        )
        return results
