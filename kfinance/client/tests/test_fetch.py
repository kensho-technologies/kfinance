from datetime import datetime
import threading
import time
from unittest import TestCase
from unittest.mock import MagicMock

import jwt
from pydantic import ValidationError
import pytest
from respx import Router

from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.kfinance import Client
from kfinance.client.models.date_and_period_models import EstimateType, Periodicity, PeriodType
from kfinance.client.models.response_models import SingleResultResp
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
    RelationshipResponse,
)
from kfinance.domains.companies.company_models import (
    CompanyDescriptions,
    CompanyIdAndName,
    CompanyOtherNames,
)
from kfinance.domains.estimates.estimates_models import (
    AnalystRecommendations,
    AnalystRecommendationsItem,
    ConsensusTargetPrice,
    ConsensusTargetPriceItem,
)
from kfinance.domains.key_developments.key_devs_models import KeyDevCategoryType
from kfinance.domains.ratings.ratings_models import IssuerRatingsResp, SecurityRatingsResp
from kfinance.domains.segments.segment_models import SegmentType


def build_mock_api_client() -> KFinanceApiClient:
    """Create a KFinanceApiClient with mocked-out fetch function."""
    kfinance_api_client = KFinanceApiClient(refresh_token="fake_refresh_token")
    kfinance_api_client.fetch = MagicMock()
    return kfinance_api_client


class TestFetchItem(TestCase):
    def setUp(self):
        """Create a KFinanceApiClient with mocked-out fetch function."""
        self.kfinance_api_client = build_mock_api_client()

    def test_fetch_id_triple(self) -> None:
        identifier = "SPGI"
        exchange_code = "NYSE"
        expected_fetch_url = (
            self.kfinance_api_client.url_base + f"id/{identifier}/exchange_code/{exchange_code}"
        )
        self.kfinance_api_client.fetch_id_triple(identifier=identifier, exchange_code=exchange_code)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_isin(self) -> None:
        security_id = 2629107
        expected_fetch_url = self.kfinance_api_client.url_base + f"isin/{security_id}"
        self.kfinance_api_client.fetch_isin(security_id=security_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_cusip(self) -> None:
        security_id = 2629107
        expected_fetch_url = self.kfinance_api_client.url_base + f"cusip/{security_id}"
        self.kfinance_api_client.fetch_cusip(security_id=security_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_history_without_dates(self) -> None:
        trading_item_id = 2629108
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}pricing/{trading_item_id}/none/none/none/adjusted"
        )
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_history(trading_item_id=trading_item_id)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_history_with_dates(self) -> None:
        trading_item_id = 2629108
        start_date = "2025-01-01"
        end_date = "2025-01-31"
        is_adjusted = False
        periodicity = Periodicity.day
        expected_fetch_url = f"{self.kfinance_api_client.url_base}pricing/{trading_item_id}/{start_date}/{end_date}/{periodicity.value}/unadjusted"

        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_history(
                trading_item_id=trading_item_id,
                is_adjusted=is_adjusted,
                start_date=start_date,
                end_date=end_date,
                periodicity=periodicity,
            )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_history_metadata(self) -> None:
        trading_item_id = 2629108
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}pricing/{trading_item_id}/metadata"
        )
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_history_metadata(trading_item_id=trading_item_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_statement(self) -> None:
        company_id = 21719
        statement_type = "BS"
        expected_url = f"{self.kfinance_api_client.url_base}statements/"
        expected_request_body = {
            "company_ids": [company_id],
            "statement_type": statement_type,
        }
        # Mock the response to have the expected PostResponse structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_statement(
            company_ids=[company_id], statement_type=statement_type
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a PostResponse
        assert "results" in result.model_dump()
        # errors field is excluded when empty

        period_type = PeriodType.quarterly
        start_year = 2024
        end_year = 2024
        start_quarter = 1
        end_quarter = 4
        expected_request_body = {
            "company_ids": [company_id],
            "statement_type": statement_type,
            "period_type": period_type.value,
            "start_year": start_year,
            "end_year": end_year,
            "start_quarter": start_quarter,
            "end_quarter": end_quarter,
        }
        # Mock the response to have the expected PostResponse structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_statement(
            company_ids=[company_id],
            statement_type=statement_type,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a PostResponse
        assert "results" in result.model_dump()
        # errors field is excluded when empty

    def test_fetch_line_item(self) -> None:
        company_id = 21719
        line_item = "cash"
        expected_url = f"{self.kfinance_api_client.url_base}line_item/"
        expected_request_body = {
            "company_ids": [company_id],
            "line_item": line_item,
        }
        # Mock the response to have the expected PostResponse structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_line_item(
            company_ids=[company_id], line_item=line_item
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a PostResponse
        assert "results" in result.model_dump()
        # errors field is excluded when empty

        period_type = PeriodType.quarterly
        start_year = 2024
        end_year = 2024
        start_quarter = 1
        end_quarter = 4
        expected_request_body = {
            "company_ids": [company_id],
            "line_item": line_item,
            "period_type": period_type.value,
            "start_year": start_year,
            "end_year": end_year,
            "start_quarter": start_quarter,
            "end_quarter": end_quarter,
        }

        # Mock the response to have the expected PostResponse structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_line_item(
            company_ids=[company_id],
            line_item=line_item,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a PostResponse
        assert "results" in result.model_dump()
        # errors field is excluded when empty

    def test_fetch_info(self) -> None:
        company_id = 21719
        expected_fetch_url = f"{self.kfinance_api_client.url_base}info/{company_id}"
        self.kfinance_api_client.fetch_info(company_id=company_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_earnings_dates(self) -> None:
        company_id = 21719
        expected_fetch_url = f"{self.kfinance_api_client.url_base}earnings/{company_id}/dates"
        self.kfinance_api_client.fetch_earnings_dates(company_id=company_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_earnings(self) -> None:
        company_id = 21719
        expected_fetch_url = f"{self.kfinance_api_client.url_base}earnings/{company_id}"
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_earnings(company_id=company_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_transcript(self) -> None:
        key_dev_id = 12345
        expected_fetch_url = f"{self.kfinance_api_client.url_base}transcript/{key_dev_id}"
        self.kfinance_api_client.fetch_transcript(key_dev_id=key_dev_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_ticker_geography_groups(self) -> None:
        country_iso_code = "USA"
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}ticker_groups/geo/country/{country_iso_code}"
        )
        self.kfinance_api_client.fetch_ticker_geography_groups(country_iso_code=country_iso_code)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)
        state_iso_code = "FL"
        expected_fetch_url = expected_fetch_url + f"/{state_iso_code}"
        self.kfinance_api_client.fetch_ticker_geography_groups(
            country_iso_code=country_iso_code, state_iso_code=state_iso_code
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_company_geography_groups(self) -> None:
        country_iso_code = "USA"
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}company_groups/geo/country/{country_iso_code}"
        )
        self.kfinance_api_client.fetch_company_geography_groups(country_iso_code=country_iso_code)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)
        state_iso_code = "FL"
        expected_fetch_url = expected_fetch_url + f"/{state_iso_code}"
        self.kfinance_api_client.fetch_company_geography_groups(
            country_iso_code=country_iso_code, state_iso_code=state_iso_code
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_ticker_exchange_groups(self) -> None:
        exchange_code = "NYSE"
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}ticker_groups/exchange/{exchange_code}"
        )
        self.kfinance_api_client.fetch_ticker_exchange_groups(exchange_code=exchange_code)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_trading_item_exchange_groups(self) -> None:
        exchange_code = "NYSE"
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}trading_item_groups/exchange/{exchange_code}"
        )
        self.kfinance_api_client.fetch_trading_item_exchange_groups(exchange_code=exchange_code)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_ticker_combined_no_parameter_exception(self) -> None:
        with self.assertRaises(
            RuntimeError, msg="Invalid parameters: No parameters provided or all set to none"
        ):
            self.kfinance_api_client.fetch_ticker_combined()

    def test_fetch_ticker_combined_state_no_country_exception(self) -> None:
        state_iso_code = "FL"
        with self.assertRaises(
            RuntimeError,
            msg="Invalid parameters: state_iso_code must be provided with a country_iso_code value",
        ):
            self.kfinance_api_client.fetch_ticker_combined(state_iso_code=state_iso_code)

    def test_fetch_ticker_combined_only_country(self) -> None:
        country_iso_code = "USA"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}ticker_groups/filters/geo/{country_iso_code.lower()}/none/simple/none/exchange/none"
        self.kfinance_api_client.fetch_ticker_combined(country_iso_code=country_iso_code)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_ticker_combined_country_and_state(self) -> None:
        country_iso_code = "USA"
        state_iso_code = "FL"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}ticker_groups/filters/geo/{country_iso_code.lower()}/{state_iso_code.lower()}/simple/none/exchange/none"
        self.kfinance_api_client.fetch_ticker_combined(
            country_iso_code=country_iso_code, state_iso_code=state_iso_code
        )
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_ticker_combined_only_simple_industry(self) -> None:
        simple_industry = "Media"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}ticker_groups/filters/geo/none/none/simple/{simple_industry.lower()}/exchange/none"
        self.kfinance_api_client.fetch_ticker_combined(simple_industry=simple_industry)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_ticker_combined_only_exchange(self) -> None:
        exchange_code = "NYSE"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}ticker_groups/filters/geo/none/none/simple/none/exchange/{exchange_code.lower()}"
        self.kfinance_api_client.fetch_ticker_combined(exchange_code=exchange_code)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_ticker_combined_all(self) -> None:
        country_iso_code = "USA"
        state_iso_code = "FL"
        simple_industry = "Media"
        exchange_code = "NYSE"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}ticker_groups/filters/geo/{country_iso_code.lower()}/{state_iso_code.lower()}/simple/{simple_industry.lower()}/exchange/{exchange_code.lower()}"
        self.kfinance_api_client.fetch_ticker_combined(
            country_iso_code=country_iso_code,
            state_iso_code=state_iso_code,
            simple_industry=simple_industry,
            exchange_code=exchange_code,
        )
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_segments(self) -> None:
        company_id = 21719
        segment_type = SegmentType.business
        expected_url = f"{self.kfinance_api_client.url_base}segments/"
        expected_request_body = {
            "company_ids": [company_id],
            "segment_type": segment_type.value,
        }
        # Mock the response to have the expected PostResponse structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_segments(
            company_ids=[company_id], segment_type=segment_type
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a PostResponse
        assert "results" in result.model_dump()
        # errors field is excluded when empty

        period_type = PeriodType.quarterly
        start_year = 2023
        end_year = 2023
        start_quarter = 1
        end_quarter = 4
        expected_request_body = {
            "company_ids": [company_id],
            "segment_type": segment_type.value,
            "period_type": period_type.value,
            "start_year": start_year,
            "end_year": end_year,
            "start_quarter": start_quarter,
            "end_quarter": end_quarter,
        }
        # Mock the response to have the expected PostResponse structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_segments(
            company_ids=[company_id],
            segment_type=segment_type,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a PostResponse
        assert "results" in result.model_dump()
        # errors field is excluded when empty

    def test_fetch_mergers_for_company(self) -> None:
        company_id = 21719
        expected_fetch_url = f"{self.kfinance_api_client.url_base}mergers/{company_id}/none/none"
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_mergers_for_company(company_id=company_id)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_mergers_with_date_range_for_company(self) -> None:
        company_id = 21719
        start_date = "2020-01-01"
        end_date = "2022-09-31"
        expected_fetch_url = (
            f"{self.kfinance_api_client.url_base}mergers/{company_id}/{start_date}/{end_date}"
        )
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_mergers_for_company(
                company_id=company_id, start_date=start_date, end_date=end_date
            )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_mergers_info(self) -> None:
        transaction_id = 554979212
        expected_fetch_url = f"{self.kfinance_api_client.url_base}mergers/info"
        expected_request_body = {
            "transaction_ids": [transaction_id],
            "include_advisors": True,
            "include_comments": True,
        }
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_mergers_info(
                transaction_ids=[transaction_id], include_advisors=True, include_comments=True
            )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_fetch_url, method="POST", request_body=expected_request_body
        )

    def test_fetch_estimate(self) -> None:
        company_id = 21719
        estimate_type = "consensus"
        expected_url = f"{self.kfinance_api_client.url_base}estimates/"
        expected_request_body = {
            "company_id": company_id,
            "estimate_type": estimate_type,
        }
        self.kfinance_api_client.fetch.return_value = {"results": {}, "errors": {}}
        result = self.kfinance_api_client.fetch_estimates(
            company_id=company_id, estimate_type=EstimateType(estimate_type)
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # Verify the result is a SingleResultResp
        expected_result_dict = {"result": None}
        assert result.model_dump() == expected_result_dict

    def test_fetch_consensus_target_price(self) -> None:
        company_id = 21719
        expected_url = (
            f"{self.kfinance_api_client.url_base}estimates/consensus_target_price/{company_id}"
        )

        self.kfinance_api_client.fetch.return_value = {
            "results": {
                str(company_id): {
                    "currency": "USD",
                    "effective_date": "2025-06-01",
                    "estimates": [
                        {"name": "Target Price Consensus Mean", "value": "520.000000"},
                    ],
                }
            },
            "errors": {},
        }

        expected_result = SingleResultResp[ConsensusTargetPrice](
            result=ConsensusTargetPrice(
                currency="USD",
                effective_date="2025-06-01",
                estimates=[
                    ConsensusTargetPriceItem(
                        name="Target Price Consensus Mean", value="520.000000"
                    ),
                ],
            ),
        )

        result = self.kfinance_api_client.fetch_consensus_target_price(
            company_id=company_id,
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_url)
        assert result == expected_result

    def test_fetch_analyst_recommendations(self) -> None:
        company_id = 21719
        expected_url = (
            f"{self.kfinance_api_client.url_base}estimates/analyst_recommendations/{company_id}"
        )

        self.kfinance_api_client.fetch.return_value = {
            "results": {
                str(company_id): {
                    "effective_date": "2025-06-01",
                    "estimates": [
                        {"name": "# of Analyst Recommendations - Buy", "value": "12"},
                    ],
                }
            },
            "errors": {},
        }

        expected_result = SingleResultResp[AnalystRecommendations](
            result=AnalystRecommendations(
                effective_date="2025-06-01",
                estimates=[
                    AnalystRecommendationsItem(
                        name="# of Analyst Recommendations - Buy", value="12"
                    ),
                ],
            ),
        )

        result = self.kfinance_api_client.fetch_analyst_recommendations(
            company_id=company_id,
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_url)
        assert result == expected_result

    def test_fetch_key_devs(self) -> None:
        company_id = 21719
        expected_url = f"{self.kfinance_api_client.url_base}key_devs/"

        # test with only required parameter
        expected_request_body = {
            "company_id": company_id,
        }
        # mock the response to have the expected structure
        self.kfinance_api_client.fetch.return_value = {"results": {}, "next_time_band": None}
        result = self.kfinance_api_client.fetch_key_devs(company_id=company_id)
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # verify the result is a KeyDevsResp
        assert "results" in result.model_dump()

        # test with all optional parameters
        start_date = "2025-01-01"
        end_date = "2025-12-31"
        key_dev_category = KeyDevCategoryType.ANNOUNCED_OR_COMPLETED_TRANSACTIONS
        expected_request_body = {
            "company_id": company_id,
            "start_date": start_date,
            "end_date": end_date,
            "key_dev_category": key_dev_category.value,
        }
        # mock the response
        self.kfinance_api_client.fetch.return_value = {"results": {}, "next_time_band": None}
        result = self.kfinance_api_client.fetch_key_devs(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            key_dev_category=key_dev_category,
        )
        self.kfinance_api_client.fetch.assert_called_with(
            expected_url, method="POST", request_body=expected_request_body
        )
        # verify the result is a KeyDevsResp
        assert "results" in result.model_dump()


class TestMarketCap:
    @pytest.mark.parametrize(
        "start_date, start_date_url", [(None, "none"), ("2025-01-01", "2025-01-01")]
    )
    @pytest.mark.parametrize(
        "end_date, end_date_url", [(None, "none"), ("2025-01-02", "2025-01-02")]
    )
    def test_fetch_market_cap(
        self, start_date: str | None, start_date_url: str, end_date: str | None, end_date_url: str
    ) -> None:
        company_id = 12345
        client = build_mock_api_client()

        expected_fetch_url = (
            f"{client.url_base}market_cap/{company_id}/{start_date_url}/{end_date_url}"
        )
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            client.fetch_market_caps_tevs_and_shares_outstanding(
                company_id=company_id, start_date=start_date, end_date=end_date
            )
        client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_permissions(self):
        client = build_mock_api_client()
        expected_fetch_url = f"{client.url_base}users/permissions"
        client.fetch_permissions()
        client.fetch.assert_called_with(expected_fetch_url)


class TestFetchCompaniesFromBusinessRelationship:
    def test_fetch_business_relationships(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN a business relationship request
        WHEN the api returns a response
        THEN the response can successfully be parsed.
        """

        http_resp = {
            "current": [{"company_name": "foo", "company_id": 883103}],
            "previous": [
                {"company_name": "bar", "company_id": 472898},
                {"company_name": "baz", "company_id": 8182358},
            ],
        }

        expected_result = RelationshipResponse(
            current=[CompanyIdAndName(company_name="foo", company_id=883103)],
            previous=[
                CompanyIdAndName(company_name="bar", company_id=472898),
                CompanyIdAndName(company_name="baz", company_id=8182358),
            ],
        )

        httpx2_mock.get(
            f"{mock_client.kfinance_api_client.url_base}relationship/{SPGI_COMPANY_ID}/{BusinessRelationshipType.supplier}",
        ).respond(json=http_resp)

        resp = mock_client.kfinance_api_client.fetch_companies_from_business_relationship(
            company_id=SPGI_COMPANY_ID, relationship_type=BusinessRelationshipType.supplier
        )
        assert resp == expected_result


class TestFetchCompanyDescriptions:
    def test_fetch_company_descriptions(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN a request to fetch company descriptions
        WHEN the api returns a response
        THEN the response can successfully be parsed into a CompanyDescriptions object.
        """

        # Truncated from actual http response
        http_resp = {
            "summary": "S&P Global Inc., together... [summary]",
            "description": "S&P Global Inc. (S&P Global), together... [description]",
        }

        expected_result = CompanyDescriptions(
            summary="S&P Global Inc., together... [summary]",
            description="S&P Global Inc. (S&P Global), together... [description]",
        )

        httpx2_mock.get(
            f"{mock_client.kfinance_api_client.url_base}info/{SPGI_COMPANY_ID}/descriptions",
        ).respond(json=http_resp)

        resp = mock_client.kfinance_api_client.fetch_company_descriptions(
            company_id=SPGI_COMPANY_ID
        )
        assert resp == expected_result


class TestFetchCompanyOtherNames:
    def test_fetch_company_other_names(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN a request to fetch a company's other names (alternate, historical, and native)
        WHEN the api returns a response
        THEN the response can be successfully parsed into a CompanyOtherNames object
        """
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

        http_resp = {
            "alternate_names": alternate_names,
            "historical_names": historical_names,
            "native_names": native_names,
        }

        expected_resp = CompanyOtherNames(
            alternate_names=alternate_names,
            historical_names=historical_names,
            native_names=native_names,
        )

        httpx2_mock.get(
            f"{mock_client.kfinance_api_client.url_base}info/{SPGI_COMPANY_ID}/names",
        ).respond(json=http_resp)

        resp = mock_client.kfinance_api_client.fetch_company_other_names(company_id=SPGI_COMPANY_ID)

        assert resp == expected_resp


class TestFetchIssuerRatings:
    def test_fetch_issuer_ratings(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN a request to fetch issuer ratings for entity IDs
        WHEN the API returns a response
        THEN the response can be successfully parsed into an IssuerRatingsResp object
        """

        entity_ids = [21719, 21835]

        http_resp = {
            "results": {
                "21719": {
                    "ratings": {
                        "ICR": {
                            "FCLONG": {
                                "last_review_date": "2025-05-22T01:13:55",
                                "latest": {
                                    "rating": "AA+",
                                    "rating_datetime": "2013-04-23T16:35:10",
                                    "rating_action_word": "New Rating",
                                    "credit_watch": None,
                                    "credit_watch_datetime": None,
                                    "outlook": "Stable",
                                    "outlook_datetime": "2013-04-23T16:35:10",
                                },
                                "history": [],
                                "source": "S&P Global",
                            }
                        }
                    }
                },
                "21835": {
                    "ratings": {
                        "ICR": {
                            "FCLONG": {
                                "last_review_date": "2025-05-22T01:13:55",
                                "latest": {
                                    "rating": "AAA",
                                    "rating_datetime": "2015-01-15T10:00:00",
                                    "rating_action_word": "Affirmed",
                                    "credit_watch": None,
                                    "credit_watch_datetime": None,
                                    "outlook": "Stable",
                                    "outlook_datetime": "2015-01-15T10:00:00",
                                },
                                "history": [],
                                "source": "S&P Global",
                            }
                        }
                    }
                },
            },
            "errors": {},
        }

        expected_resp = IssuerRatingsResp.model_validate(http_resp)

        httpx2_mock.post(
            f"{mock_client.kfinance_api_client.url_base}ratings/issuer_ratings/",
        ).respond(json=http_resp)

        resp = mock_client.kfinance_api_client.fetch_issuer_ratings(entity_ids=entity_ids)

        assert resp == expected_resp
        assert len(resp.results) == 2
        assert "21719" in resp.results
        assert "21835" in resp.results
        assert resp.errors == {}


class TestFetchSecurityRatings:
    def test_fetch_security_ratings(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN a request to fetch ratings for security IDs
        WHEN the API returns a response
        THEN the response can be successfully parsed into a SecurityRatingsResp object
        """

        security_ids = ["123456789", "XXXXX"]

        http_resp = {
            "results": {
                "123456789": {
                    "ciq_security_id": 123456789,
                    "ratings": {
                        "FCLONG": {
                            "latest": {
                                "rating": "AA+",
                                "rating_datetime": "2013-04-23T16:35:10",
                                "rating_action_word": "New Rating",
                                "credit_watch": None,
                                "credit_watch_datetime": None,
                                "outlook": "Stable",
                                "outlook_datetime": "2013-04-23T16:35:10",
                            },
                            "history": [],
                            "source": "S&P Global",
                        }
                    },
                },
                "XXXXX": {
                    "ciq_security_id": 3333333333,
                    "ratings": {
                        "FCLONG": {
                            "latest": {
                                "rating": "AA-",
                                "rating_datetime": "2016-04-23T16:35:10",
                                "rating_action_word": "NR",
                                "credit_watch": None,
                                "credit_watch_datetime": None,
                                "outlook": None,
                                "outlook_datetime": None,
                            },
                            "history": [],
                            "source": "S&P Global",
                        }
                    },
                },
            },
            "errors": {},
        }

        expected_resp = SecurityRatingsResp.model_validate(http_resp)

        httpx2_mock.post(
            f"{mock_client.kfinance_api_client.url_base}ratings/security_ratings/",
        ).respond(json=http_resp)

        resp = mock_client.kfinance_api_client.fetch_security_ratings(security_ids=security_ids)

        assert resp == expected_resp
        assert len(resp.results) == 2
        assert "123456789" in resp.results
        assert "XXXXX" in resp.results
        assert resp.errors == {}


class TestFetchRedirects:
    def test_fetch_follows_redirects(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN an endpoint that responds with a redirect (here a 307 to the same path plus a
            trailing slash)
        WHEN fetch is called
        THEN the redirect is followed and the final response is returned

        The client used to be built on requests, which follows redirects by default. httpx2
        does not (follow_redirects defaults to False), and its raise_for_status() raises
        on a 3xx. Without follow_redirects=True in fetch.py, this call would raise
        httpx2.HTTPStatusError, where it used to succeed.
        """
        url_base = mock_client.kfinance_api_client.url_base
        httpx2_mock.get(f"{url_base}info/{SPGI_COMPANY_ID}").respond(
            status_code=307, headers={"location": f"{url_base}info/{SPGI_COMPANY_ID}/"}
        )
        httpx2_mock.get(f"{url_base}info/{SPGI_COMPANY_ID}/").respond(json={"name": "S&P Global"})

        assert mock_client.kfinance_api_client.fetch_info(company_id=SPGI_COMPANY_ID) == {
            "name": "S&P Global"
        }


class TestHttpClientLifecycle:
    def test_context_manager_closes_http_client(self) -> None:
        """
        WHEN a KFinanceApiClient is used as a context manager
        THEN its pooled HTTP client is closed on exit
        """
        with KFinanceApiClient(refresh_token="fake_refresh_token") as api_client:
            assert not api_client._http_client.is_closed  # noqa: SLF001
        assert api_client._http_client.is_closed  # noqa: SLF001

    def test_cookies_do_not_persist(self, httpx2_mock: Router, mock_client: Client) -> None:
        """
        GIVEN a response that sets a cookie
        WHEN the next request is made with the same client
        THEN the cookie is not sent back

        The old requests-based client used a fresh session per request, so cookies never
        carried over. A shared httpx2.Client would keep them unless told not to.
        """
        url_base = mock_client.kfinance_api_client.url_base
        httpx2_mock.get(f"{url_base}info/1").respond(
            json={}, headers={"set-cookie": "sticky=1; Path=/"}
        )
        second = httpx2_mock.get(f"{url_base}info/2").respond(json={})

        mock_client.kfinance_api_client.fetch_info(company_id=1)
        mock_client.kfinance_api_client.fetch_info(company_id=2)

        assert "cookie" not in second.calls.last.request.headers


class TestAccessTokenRefresh:
    def test_concurrent_reads_refresh_once(self, httpx2_mock: Router) -> None:
        """
        GIVEN an expired access token
        WHEN 10 threads read access_token at the same time (as batch requests do)
        THEN the token is refreshed exactly once and every thread gets the new token

        Without the lock, every thread refreshes. The refresh also re-fetches permissions
        (mocked below), which reads access_token again on the refreshing thread. The join
        timeout makes a deadlock fail the test instead of hanging the suite.
        """
        api_client = KFinanceApiClient(refresh_token="fake_refresh_token")
        new_token = jwt.encode(
            {"exp": int(datetime(2100, 1, 1).timestamp())},
            "test-secret-at-least-32-bytes-long",
            algorithm="HS256",
        )
        refresh_calls = 0

        def slow_refresh() -> str:
            nonlocal refresh_calls
            refresh_calls += 1
            time.sleep(0.05)  # give the other threads time to pile up behind the refresh
            return new_token

        api_client._access_token_refresh_func = slow_refresh  # noqa: SLF001
        httpx2_mock.get(f"{api_client.url_base}users/permissions").respond(json={"permissions": []})

        tokens: list[str] = []
        threads = [
            threading.Thread(target=lambda: tokens.append(api_client.access_token), daemon=True)
            for _ in range(10)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        assert not any(thread.is_alive() for thread in threads), "access_token deadlocked"
        assert refresh_calls == 1
        assert tokens == [new_token] * 10
