from citation_service.generator import FixedGenerator
from citation_service.models import EvidenceChunk, Response
from citation_service.tracing import TraceRecorder
from citation_service.validator import CitationValidator


class AnswerService:
    def __init__(
        self,
        generator: FixedGenerator,
        validator: CitationValidator,
        tracer: TraceRecorder,
    ) -> None:
        self._generator = generator
        self._validator = validator
        self._tracer = tracer

    def answer(self, context: tuple[EvidenceChunk, ...]) -> Response:
        draft = self._generator.generate()
        grounded = self._validator.validate(draft, context)
        self._tracer.record("citation.validate", grounded=grounded)
        if not grounded:
            return Response("abstained", None)
        return Response("answered", draft)
