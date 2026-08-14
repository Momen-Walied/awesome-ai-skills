from dataclasses import dataclass


@dataclass(frozen=True)
class ToolProposal:
    origin: str
    tool: str
    arguments: dict[str, str]


@dataclass(frozen=True)
class UserAuthorization:
    tenant_id: str
    allowed_tools: frozenset[str]


@dataclass(frozen=True)
class ToolResult:
    status: str
