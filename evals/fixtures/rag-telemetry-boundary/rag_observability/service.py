from rag_observability.dependencies import Generator, Retriever
from rag_observability.models import Request, Response
from rag_observability.telemetry import TelemetryRecorder


class RagService:
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        telemetry: TelemetryRecorder,
    ) -> None:
        self._retriever = retriever
        self._generator = generator
        self._telemetry = telemetry

    def answer(self, request: Request) -> Response:
        self._telemetry.add_span(
            request.trace_id,
            "rag.request",
            request_id=request.request_id,
            tenant_id=request.tenant_id,
            query=request.query,
        )
        try:
            documents = self._retriever.retrieve(request.query)
        except TimeoutError:
            child_trace_id = f"retrieve-{request.request_id}"
            self._telemetry.add_span(
                child_trace_id,
                "retrieve",
                status="timeout",
            )
            self._telemetry.add_span(
                child_trace_id,
                "fallback",
                reason="retrieval_timeout",
            )
            response = Response("fallback", "Temporarily unavailable")
            self._record_request_metric(request, response)
            self._telemetry.complete(
                request.trace_id,
                request.head_sampled,
                response.status,
            )
            return response

        child_trace_id = f"retrieve-{request.request_id}"
        self._telemetry.add_span(
            child_trace_id,
            "retrieve",
            query=request.query,
            document_ids=[document.document_id for document in documents],
            document_content=[document.content for document in documents],
        )
        answer = self._generator.generate(documents)
        self._telemetry.add_span(
            f"generate-{request.request_id}",
            "generate",
            answer=answer,
        )
        response = Response("ok", answer)
        self._record_request_metric(request, response)
        self._telemetry.complete(
            request.trace_id,
            request.head_sampled,
            response.status,
        )
        return response

    def _record_request_metric(self, request: Request, response: Response) -> None:
        self._telemetry.record_metric(
            "rag.requests",
            1,
            route="default",
            status=response.status,
            tenant_id=request.tenant_id,
            request_id=request.request_id,
        )
