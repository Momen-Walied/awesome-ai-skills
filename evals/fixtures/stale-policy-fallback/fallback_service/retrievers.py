from fallback_service.models import Chunk


class PrimaryRetriever:
    def __init__(self, chunks: list[Chunk], available: bool = True) -> None:
        self._chunks = chunks
        self._available = available

    def search(self, tenant_id: str) -> list[Chunk]:
        if not self._available:
            raise TimeoutError("primary retriever timed out")
        return [chunk for chunk in self._chunks if chunk.tenant_id == tenant_id]
