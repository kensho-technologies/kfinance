from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.cusip_and_isin.cusip_and_isin_tools import (
    GetCusipFromIdentifiers,
    GetIsinFromIdentifiers,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetCusipFromIdentifiers:
    def test_get_cusip_from_identifiers(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetCusipFromIdentifiers tool
        WHEN we request the CUSIPs for multiple companies
        THEN we get back the corresponding CUSIPs
        """

        company_ids = [1, 2]
        expected_response = {"C_1": "CU1", "C_2": "CU2"}
        for security_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/cusip/{security_id}",
                json={"cusip": f"CU{security_id}"},
            )
        tool = GetCusipFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(
                identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids]
            ).model_dump(mode="json")
        )
        assert resp == expected_response


class TestGetIsinFromSecurityIds:
    def test_get_isin_from_security_ids(self, requests_mock: Mocker, mock_client: Client):
        """
        GIVEN the GetIsinFromSecurityIds tool
        WHEN we request the ISINs for multiple security ids
        THEN we get back the corresponding ISINs
        """

        company_ids = [1, 2]
        expected_response = {"C_1": "IS1", "C_2": "IS2"}
        for security_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/isin/{security_id}",
                json={"isin": f"IS{security_id}"},
            )
        tool = GetIsinFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(
                identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids]
            ).model_dump(mode="json")
        )
        assert resp == expected_response
