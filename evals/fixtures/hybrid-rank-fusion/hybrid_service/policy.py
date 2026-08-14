from collections.abc import Iterable

from hybrid_service.models import Document


def authorized_documents(
    documents: Iterable[Document], tenant_id: str
) -> list[Document]:
    return [document for document in documents if document.tenant_id == tenant_id]
