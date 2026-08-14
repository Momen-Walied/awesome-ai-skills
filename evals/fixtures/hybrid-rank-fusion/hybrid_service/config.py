from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalSettings:
    enable_hybrid: bool = True
    fusion_k: int = 60
    limit: int = 3
