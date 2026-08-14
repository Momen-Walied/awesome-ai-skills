from deadline_service.models import Response
from deadline_service.stages import Stage
from deadline_service.tracing import TraceRecorder


class RagService:
    def __init__(
        self,
        retriever: Stage,
        reranker: Stage,
        generator: Stage,
        tracer: TraceRecorder,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._generator = generator
        self._tracer = tracer

    def answer(self, budget_ms: int) -> Response:
        try:
            self._retriever.run(budget_ms)
            self._reranker.run(budget_ms)
            self._generator.run(budget_ms)
        except TimeoutError:
            self._tracer.record(
                "request.degraded",
                reason="deadline_exhausted",
            )
            return Response(None, "deadline_exhausted")
        return Response("grounded answer", "ok")
