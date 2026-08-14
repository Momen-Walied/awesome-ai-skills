import unittest

from rewrite_service.config import RewriteSettings
from rewrite_service.dependencies import QueryRewriter, Retriever
from rewrite_service.models import Document, QueryRequest, RetrievalScope
from rewrite_service.service import RetrievalService
from rewrite_service.tracing import TraceRecorder


ORIGINAL = "Reset ZX-42 without the beta procedure"
VALID_REWRITE = "ZX-42 controller reset instructions"
SECOND_VALID_REWRITE = "recovery steps for ZX-42"
THIRD_VALID_REWRITE = "ZX-42 safety reset guide"
UNSAFE_REWRITE = "controller reset instructions"
SCOPE = RetrievalScope("tenant-a", "en-GB", "2026.4", ("beta",))
REQUEST = QueryRequest(ORIGINAL, SCOPE, ("ZX-42",))
TARGET = Document("target", "tenant-a", "Authorized ZX-42 reset procedure")
ORIGINAL_ONLY = Document("original-only", "tenant-a", "Exact request evidence")
REWRITE_ONLY = Document("rewrite-only", "tenant-a", "Related reset evidence")
PRIVATE = Document("private", "tenant-b", "Private ZX-42 instructions")
RESULTS = {
    ORIGINAL: (TARGET, ORIGINAL_ONLY, PRIVATE),
    VALID_REWRITE: (TARGET, REWRITE_ONLY, PRIVATE),
    SECOND_VALID_REWRITE: (Document("second", "tenant-a", "Second route"),),
    THIRD_VALID_REWRITE: (Document("third", "tenant-a", "Third route"),),
    UNSAFE_REWRITE: (Document("unsafe", "tenant-a", "Broad controller result"),),
}


class QueryRewriteTests(unittest.TestCase):
    def make_service(
        self,
        outputs: tuple[str, ...],
        *,
        fail: bool = False,
        enable_rewrites: bool = True,
        max_rewrites: int = 2,
    ) -> tuple[RetrievalService, QueryRewriter, Retriever, TraceRecorder]:
        rewriter = QueryRewriter(outputs, fail=fail)
        retriever = Retriever(RESULTS)
        tracer = TraceRecorder()
        service = RetrievalService(
            RewriteSettings(enable_rewrites, max_rewrites),
            rewriter,
            retriever,
            tracer,
        )
        return service, rewriter, retriever, tracer

    def test_original_query_remains_first_before_a_valid_rewrite(self) -> None:
        service, _, retriever, _ = self.make_service((VALID_REWRITE,))

        service.search(REQUEST)

        self.assertEqual(
            [query for query, _ in retriever.calls], [ORIGINAL, VALID_REWRITE]
        )

    def test_rewrite_that_drops_immutable_literal_is_not_retrieved(self) -> None:
        service, _, retriever, _ = self.make_service((UNSAFE_REWRITE,))

        results = service.search(REQUEST)

        self.assertEqual([query for query, _ in retriever.calls], [ORIGINAL])
        self.assertNotIn("unsafe", [document.document_id for document in results])

    def test_rewrites_are_deduplicated_and_capped_before_retrieval(self) -> None:
        service, _, retriever, _ = self.make_service(
            (
                VALID_REWRITE,
                VALID_REWRITE,
                SECOND_VALID_REWRITE,
                THIRD_VALID_REWRITE,
            )
        )

        service.search(REQUEST)

        self.assertEqual(
            [query for query, _ in retriever.calls],
            [ORIGINAL, VALID_REWRITE, SECOND_VALID_REWRITE],
        )

    def test_zero_rewrite_limit_preserves_original_only_route(self) -> None:
        service, _, retriever, _ = self.make_service(
            (VALID_REWRITE,), max_rewrites=0
        )

        service.search(REQUEST)

        self.assertEqual([query for query, _ in retriever.calls], [ORIGINAL])

    def test_timeout_falls_back_to_original_query_and_records_reason(self) -> None:
        service, _, retriever, tracer = self.make_service((), fail=True)

        results = service.search(REQUEST)

        self.assertEqual([query for query, _ in retriever.calls], [ORIGINAL])
        self.assertEqual([document.document_id for document in results], [
            "target",
            "original-only",
        ])
        self.assertTrue(
            any(
                stage == "query.rewrite_fallback"
                and attributes["reason"] == "timeout"
                for stage, attributes in tracer.events
            )
        )

    def test_every_query_path_keeps_the_same_retrieval_scope(self) -> None:
        service, _, retriever, _ = self.make_service(
            (VALID_REWRITE, SECOND_VALID_REWRITE)
        )

        results = service.search(REQUEST)

        self.assertTrue(retriever.calls)
        self.assertTrue(all(scope == SCOPE for _, scope in retriever.calls))
        self.assertTrue(all(document.tenant_id == "tenant-a" for document in results))

    def test_evidence_is_deduplicated_by_stable_document_id(self) -> None:
        service, _, _, _ = self.make_service((VALID_REWRITE,))

        results = service.search(REQUEST)
        identifiers = [document.document_id for document in results]

        self.assertEqual(identifiers.count("target"), 1)
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_disabled_flag_preserves_original_only_rollback(self) -> None:
        service, rewriter, retriever, tracer = self.make_service(
            (VALID_REWRITE,), enable_rewrites=False
        )

        service.search(REQUEST)

        self.assertEqual(rewriter.calls, [])
        self.assertEqual([query for query, _ in retriever.calls], [ORIGINAL])
        self.assertTrue(any(stage == "retrieve.original" for stage, _ in tracer.events))

    def test_telemetry_contains_no_query_or_document_content(self) -> None:
        service, _, _, tracer = self.make_service((VALID_REWRITE,))

        service.search(REQUEST)

        serialized = repr(tracer.events)
        self.assertNotIn(ORIGINAL, serialized)
        self.assertNotIn(VALID_REWRITE, serialized)
        self.assertNotIn(TARGET.content, serialized)


if __name__ == "__main__":
    unittest.main()
