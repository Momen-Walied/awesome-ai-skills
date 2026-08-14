import unittest

from hybrid_service.config import RetrievalSettings
from hybrid_service.fusion import fuse_rankings
from hybrid_service.models import Document, ScoredHit
from hybrid_service.retrievers import FixedRankingRetriever
from hybrid_service.service import RetrievalService
from hybrid_service.tracing import TraceRecorder


DOCUMENTS = [
    Document("consensus", "tenant-a", "Reset procedure for a locked controller"),
    Document("dense-only", "tenant-a", "Recovering an unavailable controller"),
    Document("lexical-only", "tenant-a", "Controller reset glossary"),
    Document("private", "tenant-b", "Private controller recovery notes"),
]
DENSE_RANKING = (
    ("consensus", 0.99),
    ("dense-only", 0.98),
    ("private", 0.97),
)
LEXICAL_RANKING = (
    ("lexical-only", 100.0),
    ("consensus", 90.0),
    ("private", 80.0),
)


class HybridRetrievalTests(unittest.TestCase):
    def make_service(
        self, *, enable_hybrid: bool = True
    ) -> tuple[RetrievalService, TraceRecorder]:
        tracer = TraceRecorder()
        service = RetrievalService(
            DOCUMENTS,
            RetrievalSettings(enable_hybrid=enable_hybrid),
            FixedRankingRetriever(DENSE_RANKING),
            FixedRankingRetriever(LEXICAL_RANKING),
            tracer,
        )
        return service, tracer

    def test_consensus_document_wins_without_comparing_raw_scores(self) -> None:
        service, _ = self.make_service()

        results = service.search("tenant-a", "reset a locked safety controller")

        self.assertEqual(results[0].document_id, "consensus")

    def test_fusion_deduplicates_by_stable_document_id(self) -> None:
        service, _ = self.make_service()

        results = service.search("tenant-a", "reset a locked safety controller")
        identifiers = [document.document_id for document in results]

        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(identifiers.count("consensus"), 1)

    def test_fusion_uses_the_configured_rank_constant(self) -> None:
        winner = Document("winner", "tenant-a", "winner")
        late = Document("late", "tenant-a", "late")
        first = [ScoredHit(winner, 100.0)] + [
            ScoredHit(Document(f"a-{rank}", "tenant-a", "filler"), 0.0)
            for rank in range(2, 100)
        ] + [ScoredHit(late, 0.0)]
        second = [
            ScoredHit(Document(f"b-{rank}", "tenant-a", "filler"), 0.0)
            for rank in range(1, 100)
        ] + [ScoredHit(late, 0.0)]

        results = fuse_rankings((first, second), k=60, limit=1)

        self.assertEqual(results[0].document_id, "winner")

    def test_duplicate_in_one_source_contributes_only_once(self) -> None:
        duplicate = Document("duplicate", "tenant-a", "duplicate")
        consensus = Document("source-consensus", "tenant-a", "consensus")
        first = [
            ScoredHit(duplicate, 0.1),
            ScoredHit(duplicate, 0.1),
            ScoredHit(consensus, 100.0),
        ]
        second = [
            ScoredHit(Document(f"c-{rank}", "tenant-a", "filler"), 0.0)
            for rank in range(1, 100)
        ] + [ScoredHit(consensus, 100.0)]

        results = fuse_rankings((first, second), k=60, limit=1)

        self.assertEqual(results[0].document_id, "source-consensus")

    def test_hybrid_route_never_crosses_tenant_boundary(self) -> None:
        service, _ = self.make_service()

        results = service.search("tenant-a", "reset a locked safety controller")

        self.assertTrue(results)
        self.assertTrue(all(document.tenant_id == "tenant-a" for document in results))

    def test_dense_route_remains_the_disabled_flag_rollback(self) -> None:
        service, tracer = self.make_service(enable_hybrid=False)

        results = service.search("tenant-a", "reset a locked safety controller")

        self.assertEqual(results[0].document_id, "consensus")
        self.assertTrue(any(stage == "retrieve.dense" for stage, _ in tracer.events))

    def test_hybrid_trace_contains_only_bounded_route_metadata(self) -> None:
        service, tracer = self.make_service()

        service.search("tenant-a", "SYNTHETIC_QUERY_SECRET")

        self.assertEqual([stage for stage, _ in tracer.events], ["retrieve.hybrid"])
        attributes = tracer.events[0][1]
        self.assertEqual(
            set(attributes), {"dense_count", "lexical_count", "result_count"}
        )
        self.assertNotIn("SYNTHETIC_QUERY_SECRET", repr(tracer.events))


if __name__ == "__main__":
    unittest.main()
