from dataclasses import dataclass


@dataclass(frozen=True)
class RerankSettings:
    enable_reranker: bool = True
    window: int = 2
    timeout_ms: int = 40
