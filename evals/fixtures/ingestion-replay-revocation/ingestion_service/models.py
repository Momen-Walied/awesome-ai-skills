from dataclasses import dataclass


@dataclass(frozen=True)
class SourceEvent:
    sequence: int
    kind: str
    document_id: str
    tenant_id: str
    content: str | None = None


@dataclass(frozen=True)
class IndexedDocument:
    document_id: str
    tenant_id: str
    content: str
    source_sequence: int
