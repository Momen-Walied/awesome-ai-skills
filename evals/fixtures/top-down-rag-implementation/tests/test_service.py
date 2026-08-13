import unittest

from rag_service.config import RetrievalSettings
from rag_service.models import Chunk
from rag_service.service import RetrievalService
from rag_service.tracing import TraceRecorder


CHUNKS = [
    Chunk("tenant-a-manual", "tenant-a", "Calibration manual for the ZX series"),
    Chunk("tenant-a-zx42", "tenant-a", "Product page for exact SKU ZX-42"),
    Chunk("tenant-b-zx42", "tenant-b", "Private product page for exact SKU ZX-42"),
]


class RetrievalServiceTests(unittest.TestCase):
    def test_exact_sku_prefers_authorized_product_page_and_traces_strategy(self) -> None:
        tracer = TraceRecorder()
        service = RetrievalService(
            CHUNKS, RetrievalSettings(enable_exact_match=True), tracer
        )

        results = service.search("tenant-a", "ZX-42")

        self.assertEqual(results[0].chunk_id, "tenant-a-zx42")
        self.assertTrue(any(stage == "retrieve.lexical" for stage, _ in tracer.events))

    def test_exact_sku_never_crosses_tenant_boundary(self) -> None:
        service = RetrievalService(
            CHUNKS, RetrievalSettings(enable_exact_match=True), TraceRecorder()
        )

        results = service.search("tenant-a", "ZX-42")

        self.assertTrue(results)
        self.assertTrue(all(chunk.tenant_id == "tenant-a" for chunk in results))

    def test_dense_route_remains_the_disabled_flag_rollback(self) -> None:
        tracer = TraceRecorder()
        service = RetrievalService(
            CHUNKS, RetrievalSettings(enable_exact_match=False), tracer
        )

        results = service.search("tenant-a", "ZX-42")

        self.assertEqual(results[0].chunk_id, "tenant-a-manual")
        self.assertTrue(any(stage == "retrieve.dense" for stage, _ in tracer.events))


if __name__ == "__main__":
    unittest.main()
