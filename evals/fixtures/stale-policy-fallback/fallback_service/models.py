from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    tenant_id: str
    text: str


@dataclass(frozen=True)
class IndexView:
    policy_sequence: int
    chunks: tuple[Chunk, ...]
