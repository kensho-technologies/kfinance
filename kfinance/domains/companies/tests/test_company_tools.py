from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_tools import GetInfoFromIdentifiers
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetInfoFromIdentifiers:
    def test_get_info_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetInfoFromIdentifiers tool
        WHEN request info for SPGI
        THEN we get back info for SPGI
        """

        info_resp = {"name": "S&P Global Inc.", "status": "Operating"}
        expected_response = {"SPGI": info_resp}
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=info_resp,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(ToolArgsWithIdentifiers(identifiers=["SPGI"]).model_dump(mode="json"))
        assert resp == expected_response
