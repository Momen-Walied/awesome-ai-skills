from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalSettings:
    enable_exact_match: bool = False
