from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_tools import (
    GetCompanyDescriptionFromIdentifiers,
    GetCompanyDescriptionFromIdentifiersResp,
    GetCompanyOtherNamesFromIdentifiers,
    GetCompanyOtherNamesFromIdentifiersResp,
    GetCompanySummaryFromIdentifiers,
    GetCompanySummaryFromIdentifiersResp,
    GetInfoFromIdentifiers,
    GetInfoFromIdentifiersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetInfoFromIdentifiers:
    def test_get_info_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetInfoFromIdentifiers tool
        WHEN request info for SPGI and a non-existent company
        THEN we get back info for SPGI and an error for the non-existent company
        """

        info_resp = {"name": "S&P Global Inc.", "status": "Operating"}
        expected_response = GetInfoFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": info_resp},
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=info_resp,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run(
            ToolArgsWithIdentifiers(identifiers=["SPGI", "non-existent"]).model_dump(mode="json")
        )
        assert resp == expected_response


class TestGetCompanyDescriptions:
    description = "S&P Global Inc. (S&P Global), together... [description]"
    summary = "S&P Global Inc., together... [summary]"
    descriptions_data = {
        "summary": summary,
        "description": description,
    }

    def test_get_company_summary_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetCompanySummaryFromIdentifier tool
        WHEN we request the company summary (short description) for SPGI
        THEN we get back SPGI company's summary (short description)
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}/descriptions",
            # truncated from the original API response
            json=self.descriptions_data,
        )

        tool = GetCompanySummaryFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI"])
        response = tool.run(args.model_dump(mode="json"))
        expected_response = GetCompanySummaryFromIdentifiersResp.model_validate(
            {"results": {"SPGI": self.summary}}
        )
        assert response == expected_response

    def test_get_company_description_from_identifier(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetCompanyDescriptionFromIdentifier tool
        WHEN we request the company description for SPGI
        THEN we get back SPGI company's description
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}/descriptions",
            # truncated from the original API response
            json=self.descriptions_data,
        )

        tool = GetCompanyDescriptionFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI"])
        response = tool.run(args.model_dump(mode="json"))
        expected_response = GetCompanyDescriptionFromIdentifiersResp.model_validate(
            {"results": {"SPGI": self.description}}
        )
        assert response == expected_response


class TestGetCompanyOtherNames:
    alternate_names = ["S&P Global", "S&P Global, Inc.", "S&P"]
    historical_names = [
        "McGraw-Hill Publishing Company, Inc.",
        "McGraw-Hill Book Company",
        "McGraw Hill Financial, Inc.",
        "The McGraw-Hill Companies, Inc.",
    ]
    native_names = [
        {"name": "KLab Venture Partners 株式会社", "language": "Japanese"},
        {"name": "株式会社ANOBAKA", "language": "Japanese"},
        {"name": "株式会社KVP", "language": "Japanese"},
    ]

    company_other_names_info = {
        "alternate_names": alternate_names,
        "historical_names": historical_names,
        "native_names": native_names,
    }

    def test_get_company_other_names_from_identifier(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN the GetCompanyOtherNamesFromIdentifier tool
        WHEN we request the other names for SPGI
        THEN we get back SPGI's other names
        """
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}/names",
            json=self.company_other_names_info,
        )

        tool = GetCompanyOtherNamesFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI"])
        response = tool.run(args.model_dump(mode="json"))
        expected_response = GetCompanyOtherNamesFromIdentifiersResp.model_validate(
            {"results": {"SPGI": self.company_other_names_info}}
        )
        assert response == expected_response
