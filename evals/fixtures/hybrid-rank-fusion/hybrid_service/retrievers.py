from hybrid_service.models import Document, ScoredHit


class FixedRankingRetriever:
    """Deterministic stand-in for one provider-neutral retrieval route."""

    def __init__(self, ranking: tuple[tuple[str, float], ...]) -> None:
        self._ranking = ranking

    def search(self, query: str, documents: list[Document]) -> list[ScoredHit]:
        del query
        available = {document.document_id: document for document in documents}
        return [
            ScoredHit(available[document_id], score)
            for document_id, score in self._ranking
            if document_id in available
        ]
