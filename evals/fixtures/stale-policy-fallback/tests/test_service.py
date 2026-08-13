import unittest

from fallback_service.models import Chunk, IndexView
from fallback_service.retrievers import PrimaryRetriever
from fallback_service.service import RetrievalService
from fallback_service.tracing import TraceRecorder


PRIMARY_CHUNKS = [Chunk("primary-a", "tenant-a", "Current policy")]
FALLBACK_CHUNKS = (
    Chunk("fallback-a", "tenant-a", "Fallback policy"),
    Chunk("fallback-b", "tenant-b", "Private fallback policy"),
)


class RetrievalServiceTests(unittest.TestCase):
    def make_service(
        self,
        *,
        primary_available: bool,
        fallback_policy_sequence: int,
    ) -> tuple[RetrievalService, TraceRecorder]:
        tracer = TraceRecorder()
        service = RetrievalService(
            PrimaryRetriever(PRIMARY_CHUNKS, available=primary_available),
            IndexView(fallback_policy_sequence, FALLBACK_CHUNKS),
            tracer,
        )
        return service, tracer

    def test_healthy_primary_route_is_preserved(self) -> None:
        service, tracer = self.make_service(
            primary_available=True, fallback_policy_sequence=7
        )

        results = service.search("tenant-a", required_policy_sequence=7)

        self.assertEqual([chunk.chunk_id for chunk in results], ["primary-a"])
        self.assertTrue(any(stage == "retrieve.primary" for stage, _ in tracer.events))
        self.assertFalse(
            any(stage.startswith("fallback.") for stage, _ in tracer.events)
        )

    def test_fresh_fallback_is_authorized_and_traced(self) -> None:
        service, tracer = self.make_service(
            primary_available=False, fallback_policy_sequence=7
        )

        results = service.search("tenant-a", required_policy_sequence=7)

        self.assertEqual([chunk.chunk_id for chunk in results], ["fallback-a"])
        self.assertTrue(all(chunk.tenant_id == "tenant-a" for chunk in results))
        self.assertTrue(
            any(
                stage == "fallback.selected"
                and attributes["reason"] == "primary_timeout"
                for stage, attributes in tracer.events
            )
        )

    def test_stale_policy_fallback_is_blocked_and_traced(self) -> None:
        service, tracer = self.make_service(
            primary_available=False, fallback_policy_sequence=6
        )

        results = service.search("tenant-a", required_policy_sequence=7)

        self.assertEqual(results, [])
        self.assertTrue(
            any(
                stage == "fallback.blocked"
                and attributes["reason"] == "stale_policy"
                for stage, attributes in tracer.events
            )
        )

    def test_fallback_never_returns_cross_tenant_chunks(self) -> None:
        service, _ = self.make_service(
            primary_available=False, fallback_policy_sequence=7
        )

        results = service.search("tenant-a", required_policy_sequence=7)

        self.assertTrue(results)
        self.assertTrue(all(chunk.tenant_id == "tenant-a" for chunk in results))


if __name__ == "__main__":
    unittest.main()
