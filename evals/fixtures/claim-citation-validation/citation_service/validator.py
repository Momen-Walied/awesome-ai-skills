from citation_service.models import DraftAnswer, EvidenceChunk


class CitationValidator:
    def validate(
        self,
        answer: DraftAnswer,
        context: tuple[EvidenceChunk, ...],
    ) -> bool:
        context_ids = {chunk.chunk_id for chunk in context}
        return all(
            claim.citation_ids
            and set(claim.citation_ids).issubset(context_ids)
            for claim in answer.claims
        )
