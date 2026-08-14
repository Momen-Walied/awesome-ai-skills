from tool_service.models import ToolProposal, ToolResult


class ToolExecutor:
    def __init__(self) -> None:
        self.calls: list[ToolProposal] = []

    def execute(self, proposal: ToolProposal) -> ToolResult:
        self.calls.append(proposal)
        return ToolResult("executed")
