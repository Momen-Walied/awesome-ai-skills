import unittest

from rag_observability.dependencies import Generator, Retriever
from rag_observability.models import Document, Request
from rag_observability.service import RagService
from rag_observability.telemetry import TelemetryRecorder


SECRET_QUERY = "SYNTHETIC_QUERY_SECRET_7F3A"
SECRET_DOCUMENT = "SYNTHETIC_DOCUMENT_SECRET_91BD"
TENANT_ID = "synthetic-tenant-cardinality-001"
REQUEST_ID = "synthetic-request-cardinality-987"


class RagTelemetryTests(unittest.TestCase):
    def make_service(
        self,
        *,
        fail: bool = False,
    ) -> tuple[RagService, TelemetryRecorder]:
        telemetry = TelemetryRecorder()
        retriever = Retriever(
            (Document("synthetic-document-secret-42", SECRET_DOCUMENT),),
            fail=fail,
        )
        return RagService(retriever, Generator(), telemetry), telemetry

    def request(self, *, head_sampled: bool = True) -> Request:
        return Request(
            "trace-incoming-1",
            REQUEST_ID,
            TENANT_ID,
            SECRET_QUERY,
            head_sampled,
        )

    def test_sampled_request_exports_one_complete_trace(self) -> None:
        service, telemetry = self.make_service()

        service.answer(self.request())

        self.assertEqual(
            [span.name for span in telemetry.spans],
            ["rag.request", "retrieve", "generate"],
        )
        self.assertEqual(
            {span.trace_id for span in telemetry.spans},
            {"trace-incoming-1"},
        )

    def test_exported_telemetry_contains_no_sensitive_values(self) -> None:
        service, telemetry = self.make_service()

        service.answer(self.request())

        serialized = repr((telemetry.spans, telemetry.metrics))
        forbidden = (
            SECRET_QUERY,
            SECRET_DOCUMENT,
            TENANT_ID,
            REQUEST_ID,
            "synthetic-document-secret-42",
            "Grounded answer from 1 document",
        )
        leaked = [value for value in forbidden if value in serialized]
        self.assertEqual(leaked, [])

    def test_request_metric_dimensions_are_bounded(self) -> None:
        service, telemetry = self.make_service()

        service.answer(self.request())

        self.assertEqual(len(telemetry.metrics), 1)
        self.assertEqual(
            set(telemetry.metrics[0].attributes),
            {"route", "status"},
        )

    def test_non_head_sampled_fallback_keeps_complete_trace(self) -> None:
        service, telemetry = self.make_service(fail=True)

        response = service.answer(self.request(head_sampled=False))

        self.assertEqual(response.status, "fallback")
        self.assertEqual(
            [span.name for span in telemetry.spans],
            ["rag.request", "retrieve", "fallback"],
        )
        self.assertEqual(
            {span.trace_id for span in telemetry.spans},
            {"trace-incoming-1"},
        )

    def test_user_visible_paths_are_preserved(self) -> None:
        healthy, _ = self.make_service()
        fallback, _ = self.make_service(fail=True)

        self.assertEqual(healthy.answer(self.request()).status, "ok")
        self.assertEqual(
            fallback.answer(self.request()).answer,
            "Temporarily unavailable",
        )


if __name__ == "__main__":
    unittest.main()
