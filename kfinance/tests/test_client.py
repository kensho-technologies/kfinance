from unittest.mock import Mock

import pytest

from kfinance.kfinance import Client
from kfinance.models.permission_models import Permission
from kfinance.tool_calling import (
    GetBusinessRelationshipFromIdentifier,
    GetEarnings,
    GetFinancialStatementFromIdentifier,
    GetLatest,
    GetLatestEarnings,
    GetNextEarnings,
    GetTranscript,
)
from kfinance.tool_calling.shared_models import KfinanceTool


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
        # User should have access to GetBusinessRelationshipFromIdentifier
        assert GetBusinessRelationshipFromIdentifier in tool_classes
        # User should have access to functions that don't require permissions
        assert GetLatest in tool_classes
        # User should not have access to functions that require statement permissions
        assert GetFinancialStatementFromIdentifier not in tool_classes

    @pytest.mark.parametrize(
        "user_permission, expected_tool",
        [
            pytest.param(
                Permission.TranscriptsPermission, GetTranscript, id="Transcript Permissions"
            ),
            pytest.param(Permission.EarningsPermission, GetEarnings, id="Earnings Permissions"),
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
        assert GetEarnings in tool_classes
        assert GetNextEarnings in tool_classes
        assert GetLatestEarnings in tool_classes
        assert expected_tool in tool_classes
        # User should have access to functions that don't require permissions
        assert GetLatest in tool_classes
        # User should not have access to functions that require statement permissions
        assert GetFinancialStatementFromIdentifier not in tool_classes
