from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.domains.estimates.estimates_tools import (
    GetAnalystRecommendationsFromIdentifiers,
    GetAnalystRecommendationsFromIdentifiersResp,
    GetConsensusEstimatesFromIdentifiers,
    GetConsensusTargetPriceFromIdentifiers,
    GetConsensusTargetPriceFromIdentifiersResp,
    GetEstimatesFromIdentifiersArgs,
    GetEstimatesFromIdentifiersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import ToolArgsWithIdentifiers


class TestGetEstimateFromIdentifier:
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

    def test_get_estimate_from_identifier(self, mock_client: Client, requests_mock: Mocker):
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

        requests_mock.post(
            url="https://kfinance.kensho.com/api/v1/estimates/",
            json={"results": {"21719": self.estimates_response}, "errors": {}},
        )

        expected_response = GetEstimatesFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": self.estimates_response},
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
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
                {"name": "Target Price Consensus High", "value": "600.000000"},
                {"name": "Target Price Consensus Low", "value": "400.000000"},
                {"name": "Target Price Consensus Mean", "value": "520.000000"},
                {"name": "Target Price Consensus Median", "value": "525.000000"},
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

        expected_response = GetConsensusTargetPriceFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": consensus_target_price_response},
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )

        tool = GetConsensusTargetPriceFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI", "NON-EXISTENT"])
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_get_analyst_recommendations_from_identifiers(
        self, mock_client: Client, requests_mock: Mocker
    ):
        analyst_recommendations_response = {
            "effective_date": "2025-06-01",
            "estimates": [
                {"name": "# of Analyst Recommendations - Buy", "value": "12"},
                {"name": "# of Analyst Recommendations - Hold", "value": "5"},
                {"name": "# of Analyst Recommendations - Sell", "value": "1"},
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

        expected_response = GetAnalystRecommendationsFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": analyst_recommendations_response},
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )

        tool = GetAnalystRecommendationsFromIdentifiers(kfinance_client=mock_client)
        args = ToolArgsWithIdentifiers(identifiers=["SPGI", "NON-EXISTENT"])
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
