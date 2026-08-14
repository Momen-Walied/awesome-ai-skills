from hybrid_service.config import RetrievalSettings
from hybrid_service.fusion import fuse_rankings
from hybrid_service.models import Document
from hybrid_service.policy import authorized_documents
from hybrid_service.retrievers import FixedRankingRetriever
from hybrid_service.tracing import TraceRecorder


class RetrievalService:
    def __init__(
        self,
        documents: list[Document],
        settings: RetrievalSettings,
        dense: FixedRankingRetriever,
        lexical: FixedRankingRetriever,
        tracer: TraceRecorder,
    ) -> None:
        self._documents = documents
        self._settings = settings
        self._dense = dense
        self._lexical = lexical
        self._tracer = tracer

    def search(self, tenant_id: str, query: str) -> list[Document]:
        candidates = authorized_documents(self._documents, tenant_id)
        dense_hits = self._dense.search(query, candidates)
        if not self._settings.enable_hybrid:
            results = [hit.document for hit in dense_hits[: self._settings.limit]]
            self._tracer.record(
                "retrieve.dense",
                candidate_count=len(dense_hits),
                result_count=len(results),
            )
            return results

        lexical_hits = self._lexical.search(query, candidates)
        results = fuse_rankings(
            (dense_hits, lexical_hits),
            k=self._settings.fusion_k,
            limit=self._settings.limit,
        )
        self._tracer.record(
            "retrieve.hybrid",
            dense_count=len(dense_hits),
            lexical_count=len(lexical_hits),
            result_count=len(results),
        )
        return results
