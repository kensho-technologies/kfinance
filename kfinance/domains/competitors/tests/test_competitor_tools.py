from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.competitors.competitor_models import CompetitorSource
from kfinance.domains.competitors.competitor_tools import (
    GetCompetitorsFromIdentifiers,
    GetCompetitorsFromIdentifiersArgs,
)


class TestGetCompetitorsFromIdentifiers:
    def test_get_competitors_from_identifiers(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetCompetitorsFromIdentifiers tool
        WHEN we request the SPGI competitors that are named by competitors
        THEN we get back the SPGI competitors that are named by competitors
        """
        competitors_response = {
            "competitors": [
                {"company_id": 35352, "company_name": "The Descartes Systems Group Inc."},
                {"company_id": 4003514, "company_name": "London Stock Exchange Group plc"},
            ]
        }
        expected_response = {
            "SPGI": {
                "competitors": [
                    {"company_id": "C_35352", "company_name": "The Descartes Systems Group Inc."},
                    {"company_id": "C_4003514", "company_name": "London Stock Exchange Group plc"},
                ]
            }
        }

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/competitors/{SPGI_COMPANY_ID}/named_by_competitor",
            # truncated from the original API response
            json=competitors_response,
        )

        tool = GetCompetitorsFromIdentifiers(kfinance_client=mock_client)
        args = GetCompetitorsFromIdentifiersArgs(
            identifiers=["SPGI"], competitor_source=CompetitorSource.named_by_competitor
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
