from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalScope:
    tenant_id: str
    locale: str
    version: str
    excluded_terms: tuple[str, ...]


@dataclass(frozen=True)
class QueryRequest:
    text: str
    scope: RetrievalScope
    immutable_literals: tuple[str, ...]


@dataclass(frozen=True)
class Document:
    document_id: str
    tenant_id: str
    content: str
