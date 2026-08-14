from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceChunk:
    chunk_id: str
    fact_keys: frozenset[str]


@dataclass(frozen=True)
class Claim:
    text: str
    fact_key: str
    citation_ids: tuple[str, ...]


@dataclass(frozen=True)
class DraftAnswer:
    claims: tuple[Claim, ...]


@dataclass(frozen=True)
class Response:
    status: str
    answer: DraftAnswer | None
