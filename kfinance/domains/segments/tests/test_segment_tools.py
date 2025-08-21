from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.segments.segment_models import SegmentType
from kfinance.domains.segments.segment_tools import (
    GetSegmentsFromIdentifiers,
    GetSegmentsFromIdentifiersArgs,
    GetSegmentsFromIdentifiersResp,
)


class TestGetSegmentsFromIdentifier:
    segments_response = {
        "segments": {
            "2020": {
                "Commodity Insights": {
                    "CAPEX": -7000000.0,
                    "D&A": 17000000.0,
                },
                "Unallocated Assets Held for Sale": None,
            },
            "2021": {
                "Commodity Insights": {
                    "CAPEX": -2000000.0,
                    "D&A": 12000000.0,
                },
                "Unallocated Assets Held for Sale": {"Total Assets": 321000000.0},
            },
        },
    }

    def test_get_segments_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetSegmentsFromIdentifier tool
        WHEN we request the business segment for SPGI and an non-existent company
        THEN we get back the SPGI business segment and an error for the non-existent company.
        """

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/segments/{SPGI_COMPANY_ID}/business/none/none/none/none/none",
            # truncated from the original API response
            json=self.segments_response,
        )

        expected_response = GetSegmentsFromIdentifiersResp.model_validate(
            {
                "results": {"SPGI": self.segments_response},
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )

        tool = GetSegmentsFromIdentifiers(kfinance_client=mock_client)
        args = GetSegmentsFromIdentifiersArgs(
            identifiers=["SPGI", "non-existent"], segment_type=SegmentType.business
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent statement for multiple companies
        THEN we only get back the most recent statement for each company
        """

        company_ids = [1, 2]
        expected_response = GetSegmentsFromIdentifiersResp.model_validate(
            {
                "results": {
                    "C_1": {"segments": {"2021": self.segments_response["segments"]["2021"]}},
                    "C_2": {"segments": {"2021": self.segments_response["segments"]["2021"]}},
                }
            }
        )

        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/segments/{company_id}/business/none/none/none/none/none",
                json=self.segments_response,
            )

        tool = GetSegmentsFromIdentifiers(kfinance_client=mock_client)
        args = GetSegmentsFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            segment_type=SegmentType.business,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
