from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_SECURITY_ID
from kfinance.domains.cusip_and_isin.cusip_and_isin_tools import (
    GetCusipFromIdentifiers,
    GetCusipOrIsinFromIdentifiersResp,
    GetIsinFromIdentifiers,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetCusipFromIdentifiers:
    def test_get_cusip_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCusipFromIdentifiers tool
        WHEN we request the CUSIPs for SPGI including a private one
        THEN we get back the CUSIP of SPGI and an error for the private company
        """

        spgi_cusip = "78409V104"
        expected_response = GetCusipOrIsinFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": "78409V104"},
                "errors": ["private_company is a private company without a security_id."],
            }
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/cusip/{SPGI_SECURITY_ID}",
            json={"cusip": spgi_cusip},
        )
        tool = GetCusipFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(identifiers=["SPGI", "private_company"]).model_dump(mode="json")
        )
        assert resp == expected_response


class TestGetIsinFromIdentifiers:
    def test_get_isin_from_security_ids(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetIsinFromSecurityIds tool
        WHEN we request the ISINs for SPGI including a private one
        THEN we get back the ISIN of SPGI and an error for the private company
        """

        spgi_isin = "US78409V1044"

        expected_response = GetCusipOrIsinFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": "US78409V1044"},
                "errors": ["private_company is a private company without a security_id."],
            }
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/isin/{SPGI_SECURITY_ID}",
            json={"isin": spgi_isin},
        )
        tool = GetIsinFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(identifiers=["SPGI", "private_company"]).model_dump(mode="json")
        )
        assert resp == expected_response
