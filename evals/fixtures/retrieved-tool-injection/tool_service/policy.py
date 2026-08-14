from tool_service.models import ToolProposal, UserAuthorization


class ToolPolicy:
    ARGUMENT_SCHEMAS = {
        "read_document": frozenset({"tenant_id", "document_id"}),
    }

    def authorize(
        self,
        proposal: ToolProposal,
        authorization: UserAuthorization,
    ) -> tuple[bool, str]:
        if proposal.tool not in authorization.allowed_tools:
            return False, "tool_not_allowed"
        return True, "authorized"
