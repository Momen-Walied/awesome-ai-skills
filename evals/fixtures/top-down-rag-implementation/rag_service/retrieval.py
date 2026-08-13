import re

from rag_service.models import Chunk


def _semantic_terms(value: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z]+", value)
        if len(token) > 2
    }


class DenseRetriever:
    """Tiny deterministic stand-in for the fixture's current dense route."""

    def search(self, query: str, chunks: list[Chunk], limit: int = 3) -> list[Chunk]:
        query_terms = _semantic_terms(query)
        ranked = sorted(
            enumerate(chunks),
            key=lambda item: (
                -len(query_terms & _semantic_terms(item[1].text)),
                item[0],
            ),
        )
        return [chunk for _, chunk in ranked[:limit]]
