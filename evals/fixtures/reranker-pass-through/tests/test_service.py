import unittest

from rerank_service.config import RerankSettings
from rerank_service.dependencies import Reranker, Retriever
from rerank_service.models import Candidate
from rerank_service.service import RetrievalService
from rerank_service.tracing import TraceRecorder


CANDIDATES = (
    Candidate("a", "tenant-a", "First authorized result", 0.91),
    Candidate("b", "tenant-a", "Second authorized result", 0.88),
    Candidate("c", "tenant-a", "Untouched authorized tail", 0.80),
    Candidate("private", "tenant-b", "Private result", 0.99),
)


class RerankerPassThroughTests(unittest.TestCase):
    def make_service(
        self,
        output_ids: tuple[str, ...],
        *,
        fail: bool = False,
        enable_reranker: bool = True,
        window: int = 2,
        candidates: tuple[Candidate, ...] = CANDIDATES,
    ) -> tuple[RetrievalService, Retriever, Reranker, TraceRecorder]:
        retriever = Retriever(candidates)
        reranker = Reranker(output_ids, fail=fail)
        tracer = TraceRecorder()
        service = RetrievalService(
            RerankSettings(enable_reranker, window=window, timeout_ms=40),
            retriever,
            reranker,
            tracer,
        )
        return service, retriever, reranker, tracer

    def test_success_reorders_window_and_preserves_original_tail(self) -> None:
        service, _, reranker, _ = self.make_service(("b", "a"))

        results = service.search("tenant-a", "reset controller")

        self.assertEqual([candidate.document_id for candidate in results], ["b", "a", "c"])
        self.assertEqual(reranker.calls[0][1:], (("a", "b"), 40))

    def test_timeout_passes_through_complete_original_ranking(self) -> None:
        service, _, _, tracer = self.make_service((), fail=True)

        results = service.search("tenant-a", "reset controller")

        self.assertEqual([candidate.document_id for candidate in results], ["a", "b", "c"])
        self.assertTrue(
            any(
                stage == "rerank.fallback" and attributes["reason"] == "timeout"
                for stage, attributes in tracer.events
            )
        )

    def test_unknown_id_falls_back_to_original_ranking(self) -> None:
        service, _, _, tracer = self.make_service(("b", "unknown"))

        results = service.search("tenant-a", "reset controller")

        self.assertEqual([candidate.document_id for candidate in results], ["a", "b", "c"])
        self.assertTrue(
            any(
                stage == "rerank.fallback" and attributes["reason"] == "malformed_output"
                for stage, attributes in tracer.events
            )
        )

    def test_duplicate_or_missing_id_falls_back_to_original_ranking(self) -> None:
        service, _, _, _ = self.make_service(("b", "b"))

        results = service.search("tenant-a", "reset controller")

        self.assertEqual([candidate.document_id for candidate in results], ["a", "b", "c"])

    def test_empty_retrieval_skips_reranker(self) -> None:
        service, _, reranker, _ = self.make_service((), candidates=())

        results = service.search("tenant-a", "reset controller")

        self.assertEqual(results, [])
        self.assertEqual(reranker.calls, [])

    def test_zero_window_passes_through_without_calling_reranker(self) -> None:
        service, _, reranker, _ = self.make_service((), window=0)

        results = service.search("tenant-a", "reset controller")

        self.assertEqual(
            [candidate.document_id for candidate in results], ["a", "b", "c"]
        )
        self.assertEqual(reranker.calls, [])

    def test_authorization_is_preserved_before_reranking(self) -> None:
        service, _, reranker, _ = self.make_service(("b", "a"))

        results = service.search("tenant-a", "reset controller")

        self.assertNotIn("private", reranker.calls[0][1])
        self.assertTrue(all(candidate.tenant_id == "tenant-a" for candidate in results))

    def test_disabled_flag_preserves_original_ranking(self) -> None:
        service, _, reranker, tracer = self.make_service(
            ("b", "a"), enable_reranker=False
        )

        results = service.search("tenant-a", "reset controller")

        self.assertEqual([candidate.document_id for candidate in results], ["a", "b", "c"])
        self.assertEqual(reranker.calls, [])
        self.assertTrue(any(stage == "retrieve.original" for stage, _ in tracer.events))

    def test_telemetry_contains_only_bounded_reranker_metadata(self) -> None:
        service, _, _, tracer = self.make_service(("b", "a"))

        service.search("tenant-a", "SYNTHETIC_QUERY_SECRET")

        self.assertEqual([stage for stage, _ in tracer.events], ["rerank.selected"])
        self.assertEqual(set(tracer.events[0][1]), {"input_count", "output_count"})
        serialized = repr(tracer.events)
        self.assertNotIn("SYNTHETIC_QUERY_SECRET", serialized)
        self.assertNotIn("First authorized result", serialized)


if __name__ == "__main__":
    unittest.main()
