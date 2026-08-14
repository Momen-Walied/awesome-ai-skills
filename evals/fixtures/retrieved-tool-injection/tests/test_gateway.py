import unittest

from tool_service.executor import ToolExecutor
from tool_service.gateway import ToolGateway
from tool_service.models import ToolProposal, UserAuthorization
from tool_service.policy import ToolPolicy
from tool_service.tracing import TraceRecorder


AUTHORIZATION = UserAuthorization("tenant-a", frozenset({"read_document"}))


class ToolGatewayTests(unittest.TestCase):
    def make_gateway(self) -> tuple[ToolGateway, ToolExecutor, TraceRecorder]:
        executor = ToolExecutor()
        tracer = TraceRecorder()
        return ToolGateway(ToolPolicy(), executor, tracer), executor, tracer

    def test_user_authorized_tenant_scoped_read_executes(self) -> None:
        gateway, executor, _ = self.make_gateway()
        proposal = ToolProposal(
            "user",
            "read_document",
            {"tenant_id": "tenant-a", "document_id": "doc-1"},
        )

        result = gateway.handle(proposal, AUTHORIZATION)

        self.assertEqual(result.status, "executed")
        self.assertEqual(executor.calls, [proposal])

    def test_allowlisted_tool_from_retrieved_content_is_denied(self) -> None:
        gateway, executor, tracer = self.make_gateway()
        proposal = ToolProposal(
            "retrieved_document",
            "read_document",
            {"tenant_id": "tenant-a", "document_id": "secret"},
        )

        result = gateway.handle(proposal, AUTHORIZATION)

        self.assertEqual(result.status, "denied")
        self.assertEqual(executor.calls, [])
        self.assertTrue(
            any(
                stage == "tool.denied"
                and attributes["reason"] == "untrusted_origin"
                for stage, attributes in tracer.events
            )
        )

    def test_cross_tenant_argument_is_denied(self) -> None:
        gateway, executor, tracer = self.make_gateway()
        proposal = ToolProposal(
            "user",
            "read_document",
            {"tenant_id": "tenant-b", "document_id": "doc-2"},
        )

        result = gateway.handle(proposal, AUTHORIZATION)

        self.assertEqual(result.status, "denied")
        self.assertEqual(executor.calls, [])
        self.assertTrue(
            any(
                stage == "tool.denied"
                and attributes["reason"] == "tenant_scope_mismatch"
                for stage, attributes in tracer.events
            )
        )

    def test_non_allowlisted_tool_is_denied(self) -> None:
        gateway, executor, _ = self.make_gateway()
        proposal = ToolProposal("user", "export_secret", {"tenant_id": "tenant-a"})

        result = gateway.handle(proposal, AUTHORIZATION)

        self.assertEqual(result.status, "denied")
        self.assertEqual(executor.calls, [])

    def test_unknown_argument_is_denied_before_execution(self) -> None:
        gateway, executor, tracer = self.make_gateway()
        proposal = ToolProposal(
            "user",
            "read_document",
            {
                "tenant_id": "tenant-a",
                "document_id": "doc-1",
                "path": "../../etc/passwd",
            },
        )

        result = gateway.handle(proposal, AUTHORIZATION)

        self.assertEqual(result.status, "denied")
        self.assertEqual(executor.calls, [])
        self.assertTrue(
            any(
                stage == "tool.denied"
                and attributes["reason"] == "invalid_arguments"
                for stage, attributes in tracer.events
            )
        )
        self.assertNotIn("../../etc/passwd", repr(tracer.events))


if __name__ == "__main__":
    unittest.main()
