from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    tenant_id: str
    text: str
