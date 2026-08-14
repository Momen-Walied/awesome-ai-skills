from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    document_id: str
    tenant_id: str
    content: str
    retrieval_score: float
