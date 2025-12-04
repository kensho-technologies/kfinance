from urllib.parse import quote

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
        "currency": "USD",
        "periods": {
            "CY2020": {
                "period_end_date": "2020-12-31",
                "num_months": 12,
                "segments": [
                    {
                        "name": "Commodity Insights",
                        "line_items": [
                            {"name": "CAPEX", "value": "-7000000.0", "sources": []},
                            {"name": "D&A", "value": "17000000.0", "sources": []},
                        ],
                    }
                ],
            },
            "CY2021": {
                "period_end_date": "2021-12-31",
                "num_months": 12,
                "segments": [
                    {
                        "name": "Commodity Insights",
                        "line_items": [
                            {"name": "CAPEX", "value": "-2000000.0", "sources": []},
                            {"name": "D&A", "value": "12000000.0", "sources": []},
                        ],
                    },
                    {
                        "name": "Unallocated Assets Held for Sale",
                        "line_items": [
                            {"name": "Total Assets", "value": "321000000.0", "sources": []},
                        ],
                    },
                ],
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
            url=f"https://kfinance.kensho.com/api/v1/segments/absolute/{quote(f'[{SPGI_COMPANY_ID}]')}/business/none/none/none/none/none/none",
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
        WHEN we request most recent segment for multiple companies
        THEN we only get back the most recent segment for each company
        """

        company_ids = [1, 2]
        expected_response = GetSegmentsFromIdentifiersResp.model_validate(
            {
                "results": {
                    "C_1": {
                        "currency": "USD",
                        "periods": {
                            "CY2021": {
                                "period_end_date": "2021-12-31",
                                "num_months": 12,
                                "segments": self.segments_response["periods"]["CY2021"]["segments"],
                            }
                        },
                    },
                    "C_2": {
                        "currency": "USD",
                        "periods": {
                            "CY2021": {
                                "period_end_date": "2021-12-31",
                                "num_months": 12,
                                "segments": self.segments_response["periods"]["CY2021"]["segments"],
                            }
                        },
                    },
                }
            }
        )

        for company_id in company_ids:
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/segments/absolute/{quote(f'[{company_id}]')}/business/none/none/none/none/none/none",
                json=self.segments_response,
            )

        tool = GetSegmentsFromIdentifiers(kfinance_client=mock_client)
        args = GetSegmentsFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            segment_type=SegmentType.business,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response

    def test_empty_most_recent_request(self, requests_mock: Mocker, mock_client: Client) -> None:
        """
        GIVEN the GetFinancialLineItemFromIdentifiers tool
        WHEN we request most recent segment for multiple companies
        THEN we only get back the most recent segment for each company
        UNLESS no segments exist
        """

        company_ids = [1, 2]
        expected_response = GetSegmentsFromIdentifiersResp.model_validate(
            {
                "results": {
                    "C_1": {"currency": "USD", "periods": {}},
                    "C_2": {
                        "currency": "USD",
                        "periods": {
                            "CY2021": {
                                "period_end_date": "2021-12-31",
                                "num_months": 12,
                                "segments": self.segments_response["periods"]["CY2021"]["segments"],
                            }
                        },
                    },
                }
            }
        )

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/segments/absolute/{quote('[1]')}/business/none/none/none/none/none/none",
            json={"currency": "USD", "periods": {}},
        )
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/segments/absolute/{quote('[2]')}/business/none/none/none/none/none/none",
            json=self.segments_response,
        )

        tool = GetSegmentsFromIdentifiers(kfinance_client=mock_client)
        args = GetSegmentsFromIdentifiersArgs(
            identifiers=[f"{COMPANY_ID_PREFIX}{company_id}" for company_id in company_ids],
            segment_type=SegmentType.business,
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
