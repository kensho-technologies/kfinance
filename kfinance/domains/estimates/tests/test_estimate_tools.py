import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.models.date_and_period_models import EstimateType
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.estimates.estimates_models import EstimatesResp
from kfinance.domains.estimates.estimates_tools import (
    GetAnalystRecommendationsFromIdentifiers,
    GetAnalystRecommendationsFromIdentifiersResp,
    GetConsensusEstimatesFromIdentifiers,
    GetConsensusTargetPriceFromIdentifiers,
    GetConsensusTargetPriceFromIdentifiersResp,
    GetEstimatesFromIdentifiersArgs,
    GetEstimatesFromIdentifiersResp,
    fetch_estimates_from_company_id,
    get_estimates_from_identifiers,
)
from kfinance.domains.line_items.response_notes import (
    FISCAL_PERIOD_WARNING,
    FISCAL_YEAR_TERMINOLOGY_WARNING,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestEstimates:
    estimates_response = {
        "estimate_type": "consensus",
        "currency": "USD",
        "period_type": "quarterly",
        "periods": {
            "FY2025Q4": {
                "period_end_date": "2025-12-31",
                "estimates": [
                    {"name": "Book Value / Share - # of Estimates", "value": "2.000000"},
                    {"name": "Book Value / Share Consensus High", "value": "109.600000"},
                ],
            },
            "FY2026Q1": {
                "period_end_date": "2026-03-31",
                "estimates": [
                    {"name": "Book Value / Share - # of Estimates", "value": "2.000000"},
                    {"name": "Book Value / Share Consensus High", "value": "110.680000"},
                ],
            },
            "FY2026Q2": {
                "period_end_date": "2026-06-30",
                "estimates": [
                    {"name": "Book Value / Share - # of Estimates", "value": "1.000000"},
                    {"name": "Book Value / Share Consensus High", "value": "105.020000"},
                ],
            },
            "FY2026Q3": {
                "period_end_date": "2026-09-30",
                "estimates": [
                    {"name": "Book Value / Share - # of Estimates", "value": "2.000000"},
                    {"name": "Book Value / Share Consensus High", "value": "113.130000"},
                ],
            },
        },
    }

    @pytest.fixture
    def add_spgi_estimates_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI estimates."""
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): self.estimates_response},
                "errors": {},
            },
            is_optional=True,
        )

    @pytest.mark.asyncio
    async def test_fetch_estimates_from_company_id(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_estimates_mock_resp: None,
    ) -> None:
        """
        WHEN we request SPGI's estimates (using SPGI's company id)
        THEN we get back SPGI's estimates
        """

        resp = await fetch_estimates_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            estimate_type=EstimateType.consensus,
            httpx_client=httpx_client,
        )

        tool = GetConsensusEstimatesFromIdentifiers(kfinance_client=mock_client)
        args = GetEstimatesFromIdentifiersArgs(identifiers=["SPGI", "NON-EXISTENT"])
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_get_consensus_target_price_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        consensus_target_price_response = {
            "currency": "USD",
            "effective_date": "2025-06-01",
            "estimates": [
                {"Line Item": "Target Price Consensus High", "Value": "600.000000"},
                {"Line Item": "Target Price Consensus Low", "Value": "400.000000"},
                {"Line Item": "Target Price Consensus Mean", "Value": "520.000000"},
                {"Line Item": "Target Price Consensus Median", "Value": "525.000000"},
            ],
        }

        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/ids",
            json={
                "identifiers_to_id_triples": {
                    "SPGI": {
                        "company_id": 21719,
                        "security_id": 2629107,
                        "trading_item_id": 2629108,
                    }
                },
                "errors": {
                    "NON-EXISTENT": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            },
        )

        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/estimates/consensus_target_price/21719",
            json={"results": {"21719": consensus_target_price_response}, "errors": {}},
        )

        tool = GetConsensusTargetPriceFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI", "NON-EXISTENT"])
        response = tool.run(args.model_dump(mode="json"))

        assert isinstance(response, GetConsensusTargetPriceFromIdentifiersResp)
        assert "SPGI" in response.results
        assert response.results["SPGI"].currency == "USD"
        assert len(response.results["SPGI"].estimates) == 4
        assert len(response.errors) == 1

    def test_get_analyst_recommendations_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        analyst_recommendations_response = {
            "effective_date": "2025-06-01",
            "estimates": [
                {"Line Item": "# of Analyst Recommendations - Buy", "Value": "12"},
                {"Line Item": "# of Analyst Recommendations - Hold", "Value": "5"},
                {"Line Item": "# of Analyst Recommendations - Sell", "Value": "1"},
            ],
        }

        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/ids",
            json={
                "identifiers_to_id_triples": {
                    "SPGI": {
                        "company_id": 21719,
                        "security_id": 2629107,
                        "trading_item_id": 2629108,
                    }
                },
                "errors": {
                    "NON-EXISTENT": "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                },
            },
        )

        requests_mock.get(
            url="https://kfinance.kensho.com/api/v1/estimates/analyst_recommendations/21719",
            json={"results": {"21719": analyst_recommendations_response}, "errors": {}},
        )

        tool = GetAnalystRecommendationsFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI", "NON-EXISTENT"])
        response = tool.run(args.model_dump(mode="json"))

        assert isinstance(response, GetAnalystRecommendationsFromIdentifiersResp)
        assert "SPGI" in response.results
        assert len(response.results["SPGI"].estimates) == 3
        assert len(response.errors) == 1
