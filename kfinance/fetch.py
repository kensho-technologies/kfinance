from time import time
from typing import Callable, Optional

import jwt
import requests

from .constants import BusinessRelationshipType, IdentificationTriple, IndustryClassification


# version.py gets autogenerated by setuptools-scm and is not available
# during local development.
try:
    from .version import __version__ as kfinance_version
except ImportError:
    kfinance_version = "dev"


DEFAULT_API_HOST: str = "https://kfinance.kensho.com"
DEFAULT_API_VERSION: int = 1
DEFAULT_OKTA_HOST: str = "https://kensho.okta.com"
DEFAULT_OKTA_AUTH_SERVER: str = "default"


class KFinanceApiClient:
    def __init__(
        self,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        private_key: Optional[str] = None,
        api_host: str = DEFAULT_API_HOST,
        api_version: int = DEFAULT_API_VERSION,
        okta_host: str = DEFAULT_OKTA_HOST,
        okta_auth_server: str = DEFAULT_OKTA_AUTH_SERVER,
    ):
        """Configuration of KFinance Client."""
        if refresh_token is not None:
            self.refresh_token = refresh_token
            self._access_token_refresh_func: Callable[..., str] = (
                self._get_access_token_via_refresh_token
            )
        elif client_id is not None and private_key is not None:
            self.client_id = client_id
            self.private_key = private_key
            self._access_token_refresh_func = self._get_access_token_via_keypair
        else:
            raise RuntimeError("No credentials for any authentication strategy were provided")
        self.api_host = api_host
        self.api_version = api_version
        self.okta_host = okta_host
        self.okta_auth_server = okta_auth_server
        self.url_base = f"{self.api_host}/api/v{self.api_version}/"
        self._access_token_expiry = 0
        self._access_token: str | None = None
        self.user_agent_source = "object_oriented"

    @property
    def access_token(self) -> str:
        """Returns the client access token.

        If the token is not set or has expired, a new token gets fetched and returned.
        """
        if self._access_token is None or time() + 60 > self._access_token_expiry:
            self._access_token = self._access_token_refresh_func()
            self._access_token_expiry = jwt.decode(
                self._access_token,
                # nosemgrep:  python.jwt.security.unverified-jwt-decode.unverified-jwt-decode
                options={"verify_signature": False},
            ).get("exp")
        return self._access_token

    def _get_access_token_via_refresh_token(self) -> str:
        """Get an access token via oauth by submitting a refresh token."""
        response = requests.get(
            f"{self.api_host}/oauth2/refresh?refresh_token={self.refresh_token}",
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("access_token")

    def _get_access_token_via_keypair(self) -> str:
        """Get an access token via okta by submitting a registered public key."""
        iat = int(time())
        encoded = jwt.encode(
            {
                "aud": f"{self.okta_host}/oauth2/{self.okta_auth_server}/v1/token",
                "exp": iat + (60 * 60),  # expire in 60 minutes
                "iat": iat,
                "sub": self.client_id,
                "iss": self.client_id,
            },
            self.private_key,
            algorithm="RS256",
        )
        response = requests.post(
            f"{self.okta_host}/oauth2/{self.okta_auth_server}/v1/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "scope": "kensho:app:kfinance",
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": encoded,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("access_token")

    def fetch(self, url: str) -> dict:
        """Does the request and auth"""
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": f"kfinance/{kfinance_version} {self.user_agent_source}",
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def fetch_id_triple(self, identifier: str, exchange_code: Optional[str] = None) -> dict:
        """Get the ID triple from [identifier]."""
        url = f"{self.url_base}id/{identifier}"
        if exchange_code is not None:
            url = url + f"/exchange_code/{exchange_code}"
        return self.fetch(url)

    def fetch_isin(self, security_id: int) -> dict:
        """Get the ISIN."""
        url = f"{self.url_base}isin/{security_id}"
        return self.fetch(url)

    def fetch_cusip(self, security_id: int) -> dict:
        """Get the CUSIP."""
        url = f"{self.url_base}cusip/{security_id}"
        return self.fetch(url)

    def fetch_primary_security(self, company_id: int) -> dict:
        """Get the primary security of a company."""
        url = f"{self.url_base}securities/{company_id}/primary"
        return self.fetch(url)

    def fetch_securities(self, company_id: int) -> dict:
        """Get the list of securities of a company."""
        url = f"{self.url_base}securities/{company_id}"
        return self.fetch(url)

    def fetch_primary_trading_item(self, security_id: int) -> dict:
        """Get the primary trading item of a security."""
        url = f"{self.url_base}trading_items/{security_id}/primary"
        return self.fetch(url)

    def fetch_trading_items(self, security_id: int) -> dict:
        """Get the list of trading items of a security."""
        url = f"{self.url_base}trading_items/{security_id}"
        return self.fetch(url)

    def fetch_history(
        self,
        trading_item_id: int,
        is_adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        periodicity: Optional[str] = None,
    ) -> dict:
        """Get the pricing history."""
        url = (
            f"{self.url_base}pricing/{trading_item_id}/"
            f"{start_date if start_date is not None else 'none'}/"
            f"{end_date if end_date is not None else 'none'}/"
            f"{periodicity if periodicity is not None else 'none'}/"
            f"{'adjusted' if is_adjusted else 'unadjusted'}"
        )
        return self.fetch(url)

    def fetch_history_metadata(self, trading_item_id: int) -> dict[str, str]:
        """Get the pricing history metadata."""
        url = f"{self.url_base}pricing/{trading_item_id}/metadata"
        return self.fetch(url)

    def fetch_market_caps_tevs_and_shares_outstanding(
        self,
        company_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Get the market cap, TEV, and shares outstanding for a company."""
        url = (
            f"{self.url_base}market_cap/{company_id}/"
            f"{start_date if start_date is not None else 'none'}/"
            f"{end_date if end_date is not None else 'none'}"
        )
        return self.fetch(url)

    def fetch_price_chart(
        self,
        trading_item_id: int,
        is_adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        periodicity: Optional[str] = "",
    ) -> bytes:
        """Get the price chart."""
        url = (
            f"{self.url_base}price_chart/{trading_item_id}/"
            f"{start_date if start_date is not None else 'none'}/"
            f"{end_date if end_date is not None else 'none'}/"
            f"{periodicity if periodicity is not None else 'none'}/"
            f"{'adjusted' if is_adjusted else 'unadjusted'}"
        )

        response = requests.get(
            url,
            headers={
                "Content-Type": "image/png",
                "Authorization": f"Bearer {self.access_token}",
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.content

    def fetch_statement(
        self,
        company_id: int,
        statement_type: str,
        period_type: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> dict:
        """Get a specified financial statement for a specified duration."""
        url = (
            f"{self.url_base}statements/{company_id}/{statement_type}/"
            f"{period_type if period_type is not None else 'none'}/"
            f"{start_year if start_year is not None else 'none'}/"
            f"{end_year if end_year is not None else 'none'}/"
            f"{start_quarter if start_quarter is not None else 'none'}/"
            f"{end_quarter if end_quarter is not None else 'none'}"
        )
        return self.fetch(url)

    def fetch_line_item(
        self,
        company_id: int,
        line_item: str,
        period_type: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> dict:
        """Get a specified financial line item for a specified duration."""
        url = (
            f"{self.url_base}line_item/{company_id}/{line_item}/"
            f"{period_type if period_type is not None else 'none'}/"
            f"{start_year if start_year is not None else 'none'}/"
            f"{end_year if end_year is not None else 'none'}/"
            f"{start_quarter if start_quarter is not None else 'none'}/"
            f"{end_quarter if end_quarter is not None else 'none'}"
        )
        return self.fetch(url)

    def fetch_info(self, company_id: int) -> dict:
        """Get the company info."""
        url = f"{self.url_base}info/{company_id}"
        return self.fetch(url)

    def fetch_earnings_dates(self, company_id: int) -> dict:
        """Get the earnings dates."""
        url = f"{self.url_base}earnings/{company_id}/dates"
        return self.fetch(url)

    def fetch_geography_groups(
        self, country_iso_code: str, state_iso_code: Optional[str] = None, fetch_ticker: bool = True
    ) -> dict[str, list]:
        """Fetch geography groups"""
        url = f"{self.url_base}{'ticker_groups' if fetch_ticker else 'company_groups'}/geo/country/{country_iso_code}"
        if state_iso_code:
            url = url + f"/{state_iso_code}"
        return self.fetch(url)

    def fetch_ticker_geography_groups(
        self,
        country_iso_code: str,
        state_iso_code: Optional[str] = None,
    ) -> dict[str, list[IdentificationTriple]]:
        """Fetch ticker geography groups"""
        return self.fetch_geography_groups(
            country_iso_code=country_iso_code, state_iso_code=state_iso_code, fetch_ticker=True
        )

    def fetch_company_geography_groups(
        self,
        country_iso_code: str,
        state_iso_code: Optional[str] = None,
    ) -> dict[str, list[int]]:
        """Fetch company geography groups"""
        return self.fetch_geography_groups(
            country_iso_code=country_iso_code, state_iso_code=state_iso_code, fetch_ticker=False
        )

    def fetch_simple_industry_groups(
        self, simple_industry: str, fetch_ticker: bool = True
    ) -> dict[str, list]:
        """Fetch simple industry groups"""
        url = f"{self.url_base}{'ticker_groups' if fetch_ticker else 'company_groups'}/industry/simple/{simple_industry}"
        return self.fetch(url)

    def fetch_ticker_simple_industry_groups(
        self, simple_industry: str
    ) -> dict[str, list[IdentificationTriple]]:
        """Fetch ticker simple industry groups"""
        return self.fetch_simple_industry_groups(simple_industry=simple_industry, fetch_ticker=True)

    def fetch_company_simple_industry_groups(self, simple_industry: str) -> dict[str, list[int]]:
        """Fetch company simple industry groups"""
        return self.fetch_simple_industry_groups(
            simple_industry=simple_industry,
            fetch_ticker=False,
        )

    def fetch_exchange_groups(
        self, exchange_code: str, fetch_ticker: bool = True
    ) -> dict[str, list]:
        """Fetch exchange groups"""
        url = f"{self.url_base}{'ticker_groups' if fetch_ticker else 'trading_item_groups'}/exchange/{exchange_code}"
        return self.fetch(url)

    def fetch_ticker_exchange_groups(
        self, exchange_code: str
    ) -> dict[str, list[IdentificationTriple]]:
        """Fetch ticker exchange groups"""
        return self.fetch_exchange_groups(
            exchange_code=exchange_code,
            fetch_ticker=True,
        )

    def fetch_trading_item_exchange_groups(self, exchange_code: str) -> dict[str, list[int]]:
        """Fetch company exchange groups"""
        return self.fetch_exchange_groups(
            exchange_code=exchange_code,
            fetch_ticker=False,
        )

    def fetch_ticker_combined(
        self,
        country_iso_code: Optional[str] = None,
        state_iso_code: Optional[str] = None,
        simple_industry: Optional[str] = None,
        exchange_code: Optional[str] = None,
    ) -> dict[str, list[IdentificationTriple]]:
        """Fetch tickers using combined filters route"""
        if (
            country_iso_code is None
            and state_iso_code is None
            and simple_industry is None
            and exchange_code is None
        ):
            raise RuntimeError("Invalid parameters: No parameters provided or all set to none")
        elif country_iso_code is None and state_iso_code is not None:
            raise RuntimeError(
                "Invalid parameters: state_iso_code must be provided with a country_iso_code value"
            )
        else:
            url = f"{self.url_base}ticker_groups/filters/geo/{str(country_iso_code).lower()}/{str(state_iso_code).lower()}/simple/{str(simple_industry).lower()}/exchange/{str(exchange_code).lower()}"
            return self.fetch(url)

    def fetch_companies_from_business_relationship(
        self, company_id: int, relationship_type: BusinessRelationshipType
    ) -> dict[str, list[int]]:
        """Fetches a dictionary of current and previous company IDs associated with a given company ID based on the specified relationship type.

        The returned dictionary has the following structure:
        {
            "current": List[int],
            "previous": List[int]
        }

        Example: fetch_companies_from_business_relationship(company_id=1234, relationship_type="distributor") returns a dictionary of company 1234's current and previous distributors.

        :param company_id: The ID of the company for which associated companies are being fetched.
        :type company_id: int
        :param relationship_type: The type of relationship to filter by. Valid relationship types are defined in the BusinessRelationshipType class.
        :type relationship_type: BusinessRelationshipType
        :return: A dictionary containing lists of current and previous company IDs that have the specified relationship with the given company_id.
        :rtype: dict[str, list[int]]
        """
        url = f"{self.url_base}relationship/{company_id}/{relationship_type}"
        return self.fetch(url)

    def fetch_from_gics_code(
        self,
        gics_code: str,
        fetch_ticker: bool = True,
    ) -> dict[str, list]:
        """Fetches a list of companies or identification triples that are classified in the given gics_code."""
        url = f"{self.url_base}{'ticker_groups' if fetch_ticker else 'company_groups'}/industry/gics/{gics_code}"
        return self.fetch(url)

    def fetch_tickers_by_gics_code(self, gics_code: str) -> dict[str, list[IdentificationTriple]]:
        """Fetches a list of identification triples that are classified in the given gics_code.

        Returns a dictionary of shape {"tickers": List[{“company_id”: <company_id>, “security_id”: <security_id>, “trading_item_id”: <trading_item_id>}]}.
        :param gics_code: The gics_code can be either a 2-digit Sector code, 4-digit Industry Group code, 6-digit Industry code, or 8-digit Sub-industry code.
        :type gics_code: str
        :return: A dictionary containing the list of identification triple [company_id, security_id, trading_item_id] that are classified in the given gics_code.
        :rtype: dict[str, list[IdentificationTriple]]
        """
        return self.fetch_from_gics_code(gics_code=gics_code, fetch_ticker=True)

    def fetch_companies_by_gics_code(self, gics_code: str) -> dict[str, list[int]]:
        """Fetches a list of companies that are classified in the given gics_code.

        Returns a dictionary of shape {"companies": List[<company_id>]}.
        :param gics_code: The gics_code can be either a 2-digit Sector code, 4-digit Industry Group code, 6-digit Industry code, or 8-digit Sub-industry code.
        :type gics_code: str
        :return: A dictionary containing the list of companies that are classified in the given gics_code.
        :rtype: dict[str, list[int]]
        """
        return self.fetch_from_gics_code(gics_code=gics_code, fetch_ticker=False)

    def fetch_from_industry_code(
        self,
        industry_code: str,
        industry_classification: IndustryClassification,
        fetch_ticker: bool = True,
    ) -> dict[str, list]:
        """Fetches a list of companies or identification triples that are classified in the given industry_code and industry_classification."""

        url = f"{self.url_base}{'ticker_groups' if fetch_ticker else 'company_groups'}/industry/{industry_classification}/{industry_code}"
        return self.fetch(url)

    def fetch_ticker_from_industry_code(
        self,
        industry_code: str,
        industry_classification: IndustryClassification,
    ) -> dict[str, list[IdentificationTriple]]:
        """Fetches a list of identification triples that are classified in the given industry_code and industry_classification.

        Returns a dictionary of shape {"tickers": List[{“company_id”: <company_id>, “security_id”: <security_id>, “trading_item_id”: <trading_item_id>}]}.
        :param industry_code: The industry_code to filter on.
        :type industry_code: str
        :param industry_classification: The type of industry_classification to filter on, eg "SIC", "NAICS", "NACE", "ANZSIC", "SPCAPIQETF", "SPRATINGS".
        :type industry_classification: IndustryClassification
        :return: A dictionary containing the list of identification triple [company_id, security_id, trading_item_id] that are classified in the given industry_code and industry_classification.
        :rtype: dict[str, list[IdentificationTriple]]
        """
        return self.fetch_from_industry_code(
            industry_code=industry_code,
            industry_classification=industry_classification,
            fetch_ticker=True,
        )

    def fetch_company_from_industry_code(
        self,
        industry_code: str,
        industry_classification: IndustryClassification,
    ) -> dict[str, list[int]]:
        """Fetches a list of companies that are classified in the given industry_code and industry_classification.

        Returns a dictionary of shape {"companies": List[<company_id>]}.
        :param industry_code: The industry_code to filter on.
        :type industry_code: str
        :param industry_classification: The type of industry_classification to filter on, eg "SIC", "NAICS", "NACE", "ANZSIC", "SPCAPIQETF", "SPRATINGS".
        :type industry_classification: IndustryClassification
        :return: A dictionary containing the list of companies that are classified in the given industry_code and industry_classification.
        :rtype: dict[str, list[int]]
        """
        return self.fetch_from_industry_code(
            industry_code=industry_code,
            industry_classification=industry_classification,
            fetch_ticker=False,
        )
