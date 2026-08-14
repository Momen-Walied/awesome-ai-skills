from rewrite_service.models import Document, RetrievalScope


class QueryRewriter:
    def __init__(self, outputs: tuple[str, ...], *, fail: bool = False) -> None:
        self._outputs = outputs
        self._fail = fail
        self.calls: list[str] = []

    def rewrite(self, query: str) -> tuple[str, ...]:
        self.calls.append(query)
        if self._fail:
            raise TimeoutError("rewriter timed out")
        return self._outputs


class Retriever:
    def __init__(self, results: dict[str, tuple[Document, ...]]) -> None:
        self._results = results
        self.calls: list[tuple[str, RetrievalScope]] = []

    def search(self, query: str, scope: RetrievalScope) -> list[Document]:
        self.calls.append((query, scope))
        return [
            document
            for document in self._results.get(query, ())
            if document.tenant_id == scope.tenant_id
        ]
