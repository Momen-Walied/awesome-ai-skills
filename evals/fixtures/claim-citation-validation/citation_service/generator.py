from citation_service.models import DraftAnswer


class FixedGenerator:
    def __init__(self, draft: DraftAnswer) -> None:
        self._draft = draft

    def generate(self) -> DraftAnswer:
        return self._draft
