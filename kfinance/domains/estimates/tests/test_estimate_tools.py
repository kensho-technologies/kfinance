from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.client.models.date_and_period_models import EstimateType
from kfinance.domains.estimates.estimates_tools import (
    GetEstimatesFromIdentifierArgs,
    GetEstimatesFromIdentifiers,
    GetEstimatesFromIdentifiersResp
)


class TestGetEstimateFromIdentifier:
    estimates_response = {
        "meow meow meow meow meow": {}
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

        tool = GetEstimatesFromIdentifiers(kfinance_client=mock_client)
        args = GetEstimatesFromIdentifierArgs(
            identifiers=["SPGI", "NON-EXISTENT"], estimate_type=EstimateType.estimate
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
