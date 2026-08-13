import unittest

from ingestion_service.checkpoint import Checkpoint
from ingestion_service.index import SearchIndex
from ingestion_service.models import SourceEvent
from ingestion_service.pipeline import IngestionPipeline
from ingestion_service.tracing import TraceRecorder


class IngestionPipelineTests(unittest.TestCase):
    def make_pipeline(
        self,
    ) -> tuple[IngestionPipeline, SearchIndex, Checkpoint, TraceRecorder]:
        index = SearchIndex()
        checkpoint = Checkpoint()
        tracer = TraceRecorder()
        return IngestionPipeline(index, checkpoint, tracer), index, checkpoint, tracer

    def test_revocation_removes_document_and_traces_outcome(self) -> None:
        pipeline, index, checkpoint, tracer = self.make_pipeline()

        pipeline.apply(
            [
                SourceEvent(1, "upsert", "doc-1", "tenant-a", "Policy text"),
                SourceEvent(2, "revoke", "doc-1", "tenant-a"),
            ]
        )

        self.assertNotIn("doc-1", index.documents)
        self.assertEqual(checkpoint.sequence, 2)
        self.assertTrue(
            any(
                stage == "ingest.apply"
                and attributes["kind"] == "revoke"
                and attributes["outcome"] == "removed"
                for stage, attributes in tracer.events
            )
        )

    def test_hard_delete_removes_document(self) -> None:
        pipeline, index, _, _ = self.make_pipeline()

        pipeline.apply(
            [
                SourceEvent(1, "upsert", "doc-1", "tenant-a", "Policy text"),
                SourceEvent(2, "delete", "doc-1", "tenant-a"),
            ]
        )

        self.assertNotIn("doc-1", index.documents)

    def test_replay_performs_no_additional_index_mutations(self) -> None:
        pipeline, index, checkpoint, _ = self.make_pipeline()
        events = [SourceEvent(1, "upsert", "doc-1", "tenant-a", "Policy text")]

        pipeline.apply(events)
        operation_count = len(index.operations)
        pipeline.apply(events)

        self.assertEqual(len(index.operations), operation_count)
        self.assertEqual(checkpoint.sequence, 1)

    def test_later_authorized_version_can_be_indexed(self) -> None:
        pipeline, index, checkpoint, _ = self.make_pipeline()

        pipeline.apply(
            [
                SourceEvent(1, "upsert", "doc-1", "tenant-a", "Old text"),
                SourceEvent(2, "revoke", "doc-1", "tenant-a"),
                SourceEvent(3, "upsert", "doc-1", "tenant-a", "New text"),
            ]
        )

        self.assertEqual(index.documents["doc-1"].content, "New text")
        self.assertEqual(index.documents["doc-1"].source_sequence, 3)
        self.assertEqual(checkpoint.sequence, 3)

    def test_unsupported_event_does_not_advance_checkpoint(self) -> None:
        pipeline, _, checkpoint, _ = self.make_pipeline()

        with self.assertRaisesRegex(ValueError, "unsupported source event kind"):
            pipeline.apply([SourceEvent(1, "unknown", "doc-1", "tenant-a")])

        self.assertEqual(checkpoint.sequence, 0)


if __name__ == "__main__":
    unittest.main()
