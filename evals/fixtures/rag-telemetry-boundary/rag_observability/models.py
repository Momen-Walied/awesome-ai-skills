from dataclasses import dataclass


@dataclass(frozen=True)
class Request:
    trace_id: str
    request_id: str
    tenant_id: str
    query: str
    head_sampled: bool = True


@dataclass(frozen=True)
class Document:
    document_id: str
    content: str


@dataclass(frozen=True)
class Response:
    status: str
    answer: str
