from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    answer: str | None
    status: str
