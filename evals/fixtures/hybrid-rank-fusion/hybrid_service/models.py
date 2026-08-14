from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    document_id: str
    tenant_id: str
    content: str


@dataclass(frozen=True)
class ScoredHit:
    document: Document
    score: float
