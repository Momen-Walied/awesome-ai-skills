from collections.abc import Iterable

from rag_service.models import Chunk


def authorized_chunks(chunks: Iterable[Chunk], tenant_id: str) -> list[Chunk]:
    return [chunk for chunk in chunks if chunk.tenant_id == tenant_id]
