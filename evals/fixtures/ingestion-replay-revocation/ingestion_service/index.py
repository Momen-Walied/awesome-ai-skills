from ingestion_service.models import IndexedDocument, SourceEvent


class SearchIndex:
    def __init__(self) -> None:
        self.documents: dict[str, IndexedDocument] = {}
        self.operations: list[tuple[str, str, int]] = []

    def upsert(self, event: SourceEvent) -> None:
        if event.content is None:
            raise ValueError("upsert requires content")
        self.documents[event.document_id] = IndexedDocument(
            event.document_id,
            event.tenant_id,
            event.content,
            event.sequence,
        )
        self.operations.append(("upsert", event.document_id, event.sequence))

    def remove(self, event: SourceEvent) -> None:
        self.documents.pop(event.document_id, None)
        self.operations.append((event.kind, event.document_id, event.sequence))
