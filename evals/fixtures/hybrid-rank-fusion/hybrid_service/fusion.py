from hybrid_service.models import Document, ScoredHit


def fuse_rankings(
    rankings: tuple[list[ScoredHit], ...],
    *,
    k: int,
    limit: int,
) -> list[Document]:
    """Current implementation incorrectly compares provider score scales."""
    del k
    combined = [hit for ranking in rankings for hit in ranking]
    combined.sort(key=lambda hit: hit.score, reverse=True)
    return [hit.document for hit in combined[:limit]]
