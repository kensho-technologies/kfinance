from unittest.mock import Mock

from langchain_core.utils.function_calling import convert_to_openai_tool
import pytest

from kfinance.client.kfinance import Client
from kfinance.client.permission_models import Permission
from kfinance.domains.earnings.earning_tools import (
    GetEarningsFromIdentifiers,
    GetLatestEarningsFromIdentifiers,
    GetNextEarningsFromIdentifiers,
    GetTranscriptFromKeyDevId,
)
from kfinance.domains.relationships.relationship_models import (
    CR_ONLY_RELATIONSHIP_TYPES,
    RelationshipType,
)
from kfinance.domains.relationships.relationship_tools import GetRelationshipFromIdentifiers
from kfinance.domains.statements.statement_tools import GetFinancialStatementFromIdentifiers
from kfinance.integrations.tool_calling.static_tools.get_latest import GetLatest
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


class TestLangchainTools:
    @pytest.mark.parametrize(
        "fetch_value, parsed_permissions",
        [
            pytest.param(["RelationshipPermission"], {Permission.RelationshipPermission}),
            pytest.param([], set(), id="empty permissions don't raise."),
            pytest.param(
                ["InvalidPermission"], set(), id="invalid permissions get logged but don't raise."
            ),
        ],
    )
    def test_user_permissions(
        self, fetch_value: list[str], parsed_permissions: set[Permission], mock_client: Client
    ) -> None:
        """
        WHEN we fetch user permissions from the fetch_permissions endpoint
        THEN we correctly parse those permission strings into Permission enums.
        """
        mock_client.kfinance_api_client.fetch_permissions = Mock()
        mock_client.kfinance_api_client.fetch_permissions.return_value = {
            "permissions": fetch_value
        }

        assert mock_client.kfinance_api_client.user_permissions == parsed_permissions

    def test_permission_filtering(self, mock_client: Client):
        """
        GIVEN a user with limited permissions
        WHEN we filter tools by permissions
        THEN we only return tools that either don't require permissions or tools that the user
            specifically has access to.
        """

        mock_client.kfinance_api_client._user_permissions = {Permission.RelationshipPermission}  # noqa: SLF001
        tool_classes = [type(t) for t in mock_client.langchain_tools]
        # User should have access to GetRelationshipFromIdentifiers
        assert GetRelationshipFromIdentifiers in tool_classes
        # User should have access to functions that don't require permissions
        assert GetLatest in tool_classes
        # User should not have access to functions that require statement permissions
        assert GetFinancialStatementFromIdentifiers not in tool_classes

    @pytest.mark.parametrize(
        "user_permission, expected_tool",
        [
            pytest.param(
                Permission.TranscriptsPermission,
                GetTranscriptFromKeyDevId,
                id="Transcript Permissions",
            ),
            pytest.param(
                Permission.EarningsPermission, GetEarningsFromIdentifiers, id="Earnings Permissions"
            ),
        ],
    )
    def test_permission_set_handling(
        self, user_permission: Permission, expected_tool: KfinanceTool, mock_client: Client
    ):
        """
        GIVEN a user with a permission that is in a set of required permission for a tool
        WHEN we filter tools by permissions
        THEN we successfully return the correct tools that either don't require permissions or tools that the user
            specifically has access to.
        """
        mock_client.kfinance_api_client._user_permissions = {user_permission}  # noqa: SLF001
        tool_classes = [type(t) for t in mock_client.langchain_tools]
        # User should have access to GetEarnings, GetNextEarnings, GetLatestEarnings, GetTranscript
        assert GetEarningsFromIdentifiers in tool_classes
        assert GetNextEarningsFromIdentifiers in tool_classes
        assert GetLatestEarningsFromIdentifiers in tool_classes
        assert expected_tool in tool_classes
        # User should have access to functions that don't require permissions
        assert GetLatest in tool_classes
        # User should not have access to functions that require statement permissions
        assert GetFinancialStatementFromIdentifiers not in tool_classes


class TestApplyUserPermissions:
    """Tests that langchain_tools narrows each tool's LLM-facing surface to the user's permissions."""

    @staticmethod
    def relationship_tool(mock_client: Client, permissions: set[Permission]) -> KfinanceTool:
        """Build langchain tools for `permissions` and return the relationship tool."""
        mock_client.kfinance_api_client._user_permissions = permissions  # noqa: SLF001
        return next(
            tool
            for tool in mock_client.langchain_tools
            if isinstance(tool, GetRelationshipFromIdentifiers)
        )

    def test_cr_only_types_hidden_without_permission(self, mock_client: Client) -> None:
        """
        GIVEN a user without access to the Company Relationships dataset
        WHEN we generate an openai schema from the relationship tool
        THEN the Company Relationships-only types are absent from both the enum and the description.
        """
        tool = self.relationship_tool(mock_client, {Permission.RelationshipPermission})
        oai_function = convert_to_openai_tool(tool)["function"]

        enum_values = oai_function["parameters"]["properties"]["relationship_type"]["enum"]
        assert set(enum_values) == {
            relationship_type.value
            for relationship_type in set(RelationshipType) - CR_ONLY_RELATIONSHIP_TYPES
        }
        assert "supplier" in enum_values
        # creditor and borrower live in both datasets, so they stay available.
        assert {"creditor", "borrower"} <= set(enum_values)
        assert "sponsored_fund" not in enum_values
        assert "sponsored_fund" not in oai_function["description"]
        assert "pending" not in oai_function["description"]

    def test_cr_only_types_included_with_permission(self, mock_client: Client) -> None:
        """
        GIVEN a user with access to the Company Relationships dataset
        WHEN we generate an openai schema from the relationship tool
        THEN every relationship type is offered and the fund guidance is in the description.
        """
        tool = self.relationship_tool(
            mock_client, {Permission.RelationshipPermission, Permission.OnlyStaffPermission}
        )
        oai_function = convert_to_openai_tool(tool)["function"]

        enum_values = oai_function["parameters"]["properties"]["relationship_type"]["enum"]
        assert set(enum_values) == {
            relationship_type.value for relationship_type in RelationshipType
        }
        assert "sponsored_fund" in oai_function["description"]

    def test_tools_without_a_hook_are_unchanged(self, mock_client: Client) -> None:
        """
        GIVEN a tool that doesn't override apply_user_permissions
        WHEN we build langchain tools
        THEN the tool keeps its class-default name and description.
        """
        mock_client.kfinance_api_client._user_permissions = {Permission.RelationshipPermission}  # noqa: SLF001
        tool = next(tool for tool in mock_client.langchain_tools if isinstance(tool, GetLatest))

        assert tool.name == GetLatest.model_fields["name"].default
        assert tool.description == GetLatest.model_fields["description"].default
