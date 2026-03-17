import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.models.date_and_period_models import EstimateType
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.estimates.estimates_models import (
    AnalystRecommendations,
    AnalystRecommendationsResp,
    ConsensusTargetPrice,
    ConsensusTargetPriceResp,
    Estimates,
    EstimatesResp,
)
from kfinance.domains.estimates.estimates_tools import (
    GetAnalystRecommendationsFromIdentifiersResp,
    GetConsensusTargetPriceFromIdentifiersResp,
    GetEstimatesFromIdentifiersResp,
    fetch_analyst_recommendations_from_company_id,
    fetch_consensus_target_price_from_company_id,
    fetch_estimates_from_company_id,
    get_analyst_recommendations_from_identifiers,
    get_consensus_target_price_from_identifiers,
    get_estimates_from_identifiers,
)
from kfinance.domains.line_items.response_notes import (
    FISCAL_PERIOD_WARNING,
    FISCAL_YEAR_TERMINOLOGY_WARNING,
)


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

        expected_resp = EstimatesResp(
            result=Estimates.model_validate(self.estimates_response), errors=[]
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_estimates_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_estimates_mock_resp: None,
    ) -> None:
        """
        WHEN we request estimates for SPGI and a non-existent company
        THEN we get back SPGI's estimates and an error for the non-existent company
        """

        expected_resp = GetEstimatesFromIdentifiersResp(
            results={"SPGI": Estimates.model_validate(self.estimates_response)},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
            notes=[FISCAL_PERIOD_WARNING, FISCAL_YEAR_TERMINOLOGY_WARNING],
        )

        resp = await get_estimates_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            estimate_type=EstimateType.consensus,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_estimates_with_guidance_type(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request guidance estimates
        THEN we get back guidance estimates with the correct estimate_type
        """
        guidance_response = {
            **self.estimates_response,
            "estimate_type": "guidance",
        }

        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={"results": {str(SPGI_ID_TRIPLE.company_id): guidance_response}, "errors": {}},
        )

        resp = await fetch_estimates_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            estimate_type=EstimateType.guidance,
            httpx_client=httpx_client,
        )

        expected_resp = EstimatesResp(
            result=Estimates.model_validate(guidance_response), errors=[]
        )
        assert resp == expected_resp
        assert resp.result.estimate_type == EstimateType.guidance

    @pytest.mark.asyncio
    async def test_fetch_consensus_target_price_from_company_id(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request SPGI's consensus target price
        THEN we get back the target price data
        """
        consensus_target_price_response = {
            "currency": "USD",
            "effective_date": "2025-06-01",
            "estimates": [
                {"name": "Target Price Consensus High", "value": "600.000000"},
                {"name": "Target Price Consensus Low", "value": "400.000000"},
                {"name": "Target Price Consensus Mean", "value": "520.000000"},
                {"name": "Target Price Consensus Median", "value": "525.000000"},
            ],
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/estimates/consensus_target_price/{SPGI_ID_TRIPLE.company_id}",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): consensus_target_price_response},
                "errors": {},
            },
        )

        resp = await fetch_consensus_target_price_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        expected_resp = ConsensusTargetPriceResp(
            result=ConsensusTargetPrice.model_validate(consensus_target_price_response),
            errors=[],
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_consensus_target_price_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request consensus target price for SPGI and a non-existent company
        THEN we get back SPGI's target price and an error for the non-existent company
        """
        consensus_target_price_response = {
            "currency": "USD",
            "effective_date": "2025-06-01",
            "estimates": [
                {"name": "Target Price Consensus High", "value": "600.000000"},
                {"name": "Target Price Consensus Low", "value": "400.000000"},
                {"name": "Target Price Consensus Mean", "value": "520.000000"},
                {"name": "Target Price Consensus Median", "value": "525.000000"},
            ],
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/estimates/consensus_target_price/{SPGI_ID_TRIPLE.company_id}",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): consensus_target_price_response},
                "errors": {},
            },
        )

        resp = await get_consensus_target_price_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        expected_resp = GetConsensusTargetPriceFromIdentifiersResp(
            results={
                "SPGI": ConsensusTargetPrice.model_validate(consensus_target_price_response)
            },
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_fetch_analyst_recommendations_from_company_id(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request SPGI's analyst recommendations
        THEN we get back the analyst recommendations data
        """
        analyst_recommendations_response = {
            "effective_date": "2025-06-01",
            "estimates": [
                {"name": "# of Analyst Recommendations - Buy", "value": "12"},
                {"name": "# of Analyst Recommendations - Hold", "value": "5"},
                {"name": "# of Analyst Recommendations - Sell", "value": "1"},
            ],
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/estimates/analyst_recommendations/{SPGI_ID_TRIPLE.company_id}",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): analyst_recommendations_response},
                "errors": {},
            },
        )

        resp = await fetch_analyst_recommendations_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        expected_resp = AnalystRecommendationsResp(
            result=AnalystRecommendations.model_validate(analyst_recommendations_response),
            errors=[],
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_analyst_recommendations_from_identifiers(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """
        WHEN we request analyst recommendations for SPGI and a non-existent company
        THEN we get back SPGI's recommendations and an error for the non-existent company
        """
        analyst_recommendations_response = {
            "effective_date": "2025-06-01",
            "estimates": [
                {"name": "# of Analyst Recommendations - Buy", "value": "12"},
                {"name": "# of Analyst Recommendations - Hold", "value": "5"},
                {"name": "# of Analyst Recommendations - Sell", "value": "1"},
            ],
        }

        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/estimates/analyst_recommendations/{SPGI_ID_TRIPLE.company_id}",
            json={
                "results": {str(SPGI_ID_TRIPLE.company_id): analyst_recommendations_response},
                "errors": {},
            },
        )

        resp = await get_analyst_recommendations_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        expected_resp = GetAnalystRecommendationsFromIdentifiersResp(
            results={
                "SPGI": AnalystRecommendations.model_validate(analyst_recommendations_response)
            },
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        assert resp == expected_resp
