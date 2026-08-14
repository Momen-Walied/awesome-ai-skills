from rerank_service.models import Candidate


class Retriever:
    def __init__(self, candidates: tuple[Candidate, ...]) -> None:
        self._candidates = candidates
        self.calls: list[tuple[str, str]] = []

    def search(self, tenant_id: str, query: str) -> list[Candidate]:
        self.calls.append((tenant_id, query))
        return [
            candidate
            for candidate in self._candidates
            if candidate.tenant_id == tenant_id
        ]


class Reranker:
    def __init__(self, output_ids: tuple[str, ...], *, fail: bool = False) -> None:
        self._output_ids = output_ids
        self._fail = fail
        self.calls: list[tuple[str, tuple[str, ...], int]] = []

    def rerank(
        self,
        query: str,
        candidates: list[Candidate],
        timeout_ms: int,
    ) -> tuple[str, ...]:
        self.calls.append(
            (query, tuple(candidate.document_id for candidate in candidates), timeout_ms)
        )
        if self._fail:
            raise TimeoutError("reranker timed out")
        return self._output_ids
