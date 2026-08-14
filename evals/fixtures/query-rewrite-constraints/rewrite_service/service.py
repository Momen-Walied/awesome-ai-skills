from rewrite_service.config import RewriteSettings
from rewrite_service.dependencies import QueryRewriter, Retriever
from rewrite_service.models import Document, QueryRequest
from rewrite_service.tracing import TraceRecorder


class RetrievalService:
    def __init__(
        self,
        settings: RewriteSettings,
        rewriter: QueryRewriter,
        retriever: Retriever,
        tracer: TraceRecorder,
    ) -> None:
        self._settings = settings
        self._rewriter = rewriter
        self._retriever = retriever
        self._tracer = tracer

    def search(self, request: QueryRequest) -> list[Document]:
        if not self._settings.enable_rewrites:
            results = self._retriever.search(request.text, request.scope)
            self._tracer.record("retrieve.original", result_count=len(results))
            return results

        try:
            rewrites = self._rewriter.rewrite(request.text)
        except TimeoutError:
            self._tracer.record("query.rewrite_fallback", reason="timeout")
            return []

        results: list[Document] = []
        for rewrite in rewrites:
            results.extend(self._retriever.search(rewrite, request.scope))
        self._tracer.record(
            "query.rewrite",
            rewrite_count=len(rewrites),
            result_count=len(results),
        )
        return results
