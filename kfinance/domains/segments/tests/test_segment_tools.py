from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.segments.segment_models import SegmentType
from kfinance.domains.segments.segment_tools import (
    GetSegmentsFromIdentifiers,
    GetSegmentsFromIdentifiersArgs,
)


class TestGetSegmentsFromIdentifier:
    def test_get_segments_from_identifier(self, mock_client: Client, requests_mock: Mocker):
        """
        GIVEN the GetSegmentsFromIdentifier tool
        WHEN we request the SPGI business segment
        THEN we get back the SPGI business segment
        """

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
        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/segments/{SPGI_COMPANY_ID}/business/none/none/none/none/none",
            # truncated from the original API response
            json=segments_response,
        )

        expected_response = {"SPGI": segments_response["segments"]}

        tool = GetSegmentsFromIdentifiers(kfinance_client=mock_client)
        args = GetSegmentsFromIdentifiersArgs(
            identifiers=["SPGI"], segment_type=SegmentType.business
        )
        response = tool.run(args.model_dump(mode="json"))
        assert response == expected_response
