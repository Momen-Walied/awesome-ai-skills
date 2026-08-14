from rag_observability.models import Document


class Retriever:
    def __init__(self, documents: tuple[Document, ...], fail: bool = False) -> None:
        self._documents = documents
        self._fail = fail

    def retrieve(self, query: str) -> tuple[Document, ...]:
        if self._fail:
            raise TimeoutError("retrieval timed out")
        return self._documents


class Generator:
    def generate(self, documents: tuple[Document, ...]) -> str:
        return f"Grounded answer from {len(documents)} document"
