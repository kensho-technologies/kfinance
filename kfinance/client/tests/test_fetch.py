from unittest import TestCase
from unittest.mock import MagicMock

from pydantic import ValidationError
import pytest
from requests_mock import Mocker

from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.kfinance import Client
from kfinance.client.models.date_and_period_models import Periodicity, PeriodType
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
    RelationshipResponse,
)
from kfinance.domains.companies.company_models import CompanyIdAndName


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
        self.kfinance_api_client.fetch_history_metadata(trading_item_id=trading_item_id)
        self.kfinance_api_client.fetch.assert_called_once_with(expected_fetch_url)

    def test_fetch_statement(self) -> None:
        company_id = 21719
        statement_type = "BS"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}statements/{company_id}/{statement_type}/none/none/none/none/none"
        self.kfinance_api_client.fetch_statement(
            company_id=company_id, statement_type=statement_type
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)
        period_type = PeriodType.quarterly
        start_year = 2024
        end_year = 2024
        start_quarter = 1
        end_quarter = 4
        expected_fetch_url = f"{self.kfinance_api_client.url_base}statements/{company_id}/{statement_type}/{period_type.value}/{start_year}/{end_year}/{start_quarter}/{end_quarter}"
        self.kfinance_api_client.fetch_statement(
            company_id=company_id,
            statement_type=statement_type,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_line_item(self) -> None:
        company_id = 21719
        line_item = "cash"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}line_item/{company_id}/{line_item}/none/none/none/none/none"
        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_line_item(company_id=company_id, line_item=line_item)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)
        period_type = PeriodType.quarterly
        start_year = 2024
        end_year = 2024
        start_quarter = 1
        end_quarter = 4
        expected_fetch_url = f"{self.kfinance_api_client.url_base}line_item/{company_id}/{line_item}/{period_type.value}/{start_year}/{end_year}/{start_quarter}/{end_quarter}"

        # Validation error is ok, we only care that the function was called with the correct url
        with pytest.raises(ValidationError):
            self.kfinance_api_client.fetch_line_item(
                company_id=company_id,
                line_item=line_item,
                period_type=period_type,
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

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
        segment_type = "business"
        expected_fetch_url = f"{self.kfinance_api_client.url_base}segments/{company_id}/{segment_type}/none/none/none/none/none"
        self.kfinance_api_client.fetch_segments(company_id=company_id, segment_type=segment_type)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)
        period_type = PeriodType.quarterly
        start_year = 2023
        end_year = 2023
        start_quarter = 1
        end_quarter = 4
        expected_fetch_url = f"{self.kfinance_api_client.url_base}segments/{company_id}/{segment_type}/{period_type.value}/{start_year}/{end_year}/{start_quarter}/{end_quarter}"
        self.kfinance_api_client.fetch_segments(
            company_id=company_id,
            segment_type=segment_type,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_mergers_for_company(self) -> None:
        company_id = 21719
        expected_fetch_url = f"{self.kfinance_api_client.url_base}mergers/{company_id}"
        self.kfinance_api_client.fetch_mergers_for_company(company_id=company_id)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_merger_info(self) -> None:
        transaction_id = 554979212
        expected_fetch_url = f"{self.kfinance_api_client.url_base}merger/info/{transaction_id}"
        self.kfinance_api_client.fetch_merger_info(transaction_id=transaction_id)
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)

    def test_fetch_advisors_for_company_in_merger(self) -> None:
        transaction_id = 554979212
        advised_company_id = 251994106
        expected_fetch_url = f"{self.kfinance_api_client.url_base}merger/info/{transaction_id}/advisors/{advised_company_id}"
        self.kfinance_api_client.fetch_advisors_for_company_in_merger(
            transaction_id=transaction_id, advised_company_id=advised_company_id
        )
        self.kfinance_api_client.fetch.assert_called_with(expected_fetch_url)


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
    def test_fetch_business_relationships(self, requests_mock: Mocker, mock_client: Client) -> None:
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

        requests_mock.get(
            url=f"{mock_client.kfinance_api_client.url_base}relationship/{SPGI_COMPANY_ID}/{BusinessRelationshipType.supplier}",
            json=http_resp,
        )

        resp = mock_client.kfinance_api_client.fetch_companies_from_business_relationship(
            company_id=SPGI_COMPANY_ID, relationship_type=BusinessRelationshipType.supplier
        )
        assert resp == expected_result
