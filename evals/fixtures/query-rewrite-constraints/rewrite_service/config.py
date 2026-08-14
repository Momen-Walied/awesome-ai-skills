from dataclasses import dataclass


@dataclass(frozen=True)
class RewriteSettings:
    enable_rewrites: bool = True
    max_rewrites: int = 2
