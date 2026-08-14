import unittest

from citation_service.generator import FixedGenerator
from citation_service.models import Claim, DraftAnswer, EvidenceChunk
from citation_service.service import AnswerService
from citation_service.tracing import TraceRecorder
from citation_service.validator import CitationValidator


CONTEXT = (
    EvidenceChunk("pricing", frozenset({"price"})),
    EvidenceChunk("warranty", frozenset({"warranty_period"})),
)


class AnswerServiceTests(unittest.TestCase):
    def answer(self, claim: Claim) -> tuple[str, TraceRecorder]:
        tracer = TraceRecorder()
        service = AnswerService(
            FixedGenerator(DraftAnswer((claim,))),
            CitationValidator(),
            tracer,
        )
        return service.answer(CONTEXT).status, tracer

    def test_supported_claim_remains_answered(self) -> None:
        status, _ = self.answer(Claim("It costs 20 USD", "price", ("pricing",)))

        self.assertEqual(status, "answered")

    def test_valid_but_unrelated_citation_abstains(self) -> None:
        status, _ = self.answer(
            Claim("The warranty is two years", "warranty_period", ("pricing",))
        )

        self.assertEqual(status, "abstained")

    def test_missing_citation_abstains(self) -> None:
        status, _ = self.answer(Claim("It costs 20 USD", "price", ()))

        self.assertEqual(status, "abstained")

    def test_citation_outside_context_abstains(self) -> None:
        status, _ = self.answer(Claim("It costs 20 USD", "price", ("private",)))

        self.assertEqual(status, "abstained")

    def test_validation_outcome_is_traced(self) -> None:
        _, tracer = self.answer(
            Claim("The warranty is two years", "warranty_period", ("pricing",))
        )

        self.assertTrue(
            any(
                stage == "citation.validate" and attributes["grounded"] is False
                for stage, attributes in tracer.events
            )
        )
        self.assertNotIn("The warranty is two years", repr(tracer.events))


if __name__ == "__main__":
    unittest.main()
