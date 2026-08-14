from tool_service.executor import ToolExecutor
from tool_service.models import ToolProposal, ToolResult, UserAuthorization
from tool_service.policy import ToolPolicy
from tool_service.tracing import TraceRecorder


class ToolGateway:
    def __init__(
        self,
        policy: ToolPolicy,
        executor: ToolExecutor,
        tracer: TraceRecorder,
    ) -> None:
        self._policy = policy
        self._executor = executor
        self._tracer = tracer

    def handle(
        self,
        proposal: ToolProposal,
        authorization: UserAuthorization,
    ) -> ToolResult:
        allowed, reason = self._policy.authorize(proposal, authorization)
        if not allowed:
            self._tracer.record("tool.denied", tool=proposal.tool, reason=reason)
            return ToolResult("denied")
        result = self._executor.execute(proposal)
        self._tracer.record("tool.executed", tool=proposal.tool)
        return result
