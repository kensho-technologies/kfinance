from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from functools import cached_property
from io import BytesIO
import logging
import re
from sys import stdout
from typing import TYPE_CHECKING, Any, Callable, Iterable, NamedTuple, Optional
from urllib.parse import urljoin
import webbrowser

from langchain_core.utils.function_calling import convert_to_openai_tool
import numpy as np
import pandas as pd
from PIL.Image import Image, open as image_open

from .batch_request_handling import add_methods_of_singular_class_to_iterable_class
from .constants import HistoryMetadata, IdentificationTriple, LatestPeriods, YearAndQuarter
from .fetch import (
    DEFAULT_API_HOST,
    DEFAULT_API_VERSION,
    DEFAULT_OKTA_AUTH_SERVER,
    DEFAULT_OKTA_HOST,
    KFinanceApiClient,
)
from .meta_classes import (
    CompanyFunctionsMetaClass,
    DelegatedCompanyFunctionsMetaClass,
)
from .prompt import PROMPT
from .server_thread import ServerThread


if TYPE_CHECKING:
    from kfinance.tool_calling.shared_models import KfinanceTool

logger = logging.getLogger(__name__)


class TradingItem:
    """Trading Class

    :param kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param trading_item_id: The S&P CIQ Trading Item ID
    :type trading_item_id: int
    """

    def __init__(
        self,
        kfinance_api_client: KFinanceApiClient,
        trading_item_id: int,
    ):
        """Initialize the trading item object

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param trading_item_id: The S&P CIQ Trading Item ID
        :type trading_item_id: int
        """
        self.kfinance_api_client = kfinance_api_client
        self.trading_item_id = trading_item_id
        self.ticker: Optional[str] = None
        self.exchange_code: Optional[str] = None

    def __str__(self) -> str:
        """String representation for the company object"""
        return f"{type(self).__module__}.{type(self).__qualname__} of {self.trading_item_id}"

    @staticmethod
    def from_ticker(
        kfinance_api_client: KFinanceApiClient, ticker: str, exchange_code: Optional[str] = None
    ) -> "TradingItem":
        """Return TradingItem object from ticker

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param ticker: the ticker symbol
        :type ticker: str
        :param exchange_code: The exchange code identifying which exchange the ticker is on.
        :type exchange_code: str, optional
        """
        trading_item_id = kfinance_api_client.fetch_id_triple(ticker, exchange_code)[
            "trading_item_id"
        ]
        trading_item = TradingItem(kfinance_api_client, trading_item_id)
        trading_item.ticker = ticker
        trading_item.exchange_code = exchange_code
        return trading_item

    @cached_property
    def trading_item_id(self) -> int:
        """Get the trading item id for the object

        :return: the CIQ trading item id
        :rtype: int
        """
        return self.trading_item_id

    @cached_property
    def history_metadata(self) -> HistoryMetadata:
        """Get information about exchange and quotation

        :return: A dict containing data about the currency, symbol, exchange, type of instrument, and the first trading date
        :rtype: HistoryMetadata
        """
        metadata = self.kfinance_api_client.fetch_history_metadata(self.trading_item_id)
        if self.exchange_code is None:
            self.exchange_code = metadata["exchange_name"]
        return {
            "currency": metadata["currency"],
            "symbol": metadata["symbol"],
            "exchange_name": metadata["exchange_name"],
            "instrument_type": metadata["instrument_type"],
            "first_trade_date": datetime.strptime(metadata["first_trade_date"], "%Y-%m-%d").date(),
        }

    def history(
        self,
        periodicity: str = "day",
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves the historical price data for a given asset over a specified date range.

        :param str periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :param Optional[bool] adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :param Optional[str] start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :param Optional[str] end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :return: A pd.DataFrame containing historical price data with columns corresponding to the specified periodicity, with Date as the index, and columns "open", "high", "low", "close", "volume" in type decimal. The Date index is a string that depends on the periodicity. If periodicity="day", the Date index is the day in format "YYYY-MM-DD", eg "2024-05-13" If periodicity="week", the Date index is the week number of the year in format "YYYY Week ##", eg "2024 Week 2" If periodicity="month", the Date index is the month name of the year in format "<Month> YYYY", eg "January 2024". If periodicity="year", the Date index is the year in format "YYYY", eg "2024".
        :rtype: pd.DataFrame
        """
        if periodicity not in {"day", "week", "month", "year"}:
            raise RuntimeError(f"Periodicity type {periodicity} is not valid.")

        if start_date and end_date:
            if (
                datetime.strptime(start_date, "%Y-%m-%d").date()
                > datetime.strptime(end_date, "%Y-%m-%d").date()
            ):
                return pd.DataFrame()

        return (
            pd.DataFrame(
                self.kfinance_api_client.fetch_history(
                    trading_item_id=self.trading_item_id,
                    is_adjusted=adjusted,
                    start_date=start_date,
                    end_date=end_date,
                    periodicity=periodicity,
                )["prices"]
            )
            .set_index("date")
            .apply(pd.to_numeric)
            .replace(np.nan, None)
        )

    def price_chart(
        self,
        periodicity: str = "day",
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Image:
        """Get the price chart.

        :param str periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :param Optional[bool] adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :param Optional[str] start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :param Optional[str] end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :return: An image showing the price chart of the trading item
        :rtype: Image
        """

        if periodicity not in {"day", "week", "month", "year"}:
            raise RuntimeError(f"Periodicity type {periodicity} is not valid.")

        if start_date and end_date:
            if (
                datetime.strptime(start_date, "%Y-%m-%d").date()
                > datetime.strptime(end_date, "%Y-%m-%d").date()
            ):
                return pd.DataFrame()

        content = self.kfinance_api_client.fetch_price_chart(
            trading_item_id=self.trading_item_id,
            is_adjusted=adjusted,
            start_date=start_date,
            end_date=end_date,
            periodicity=periodicity,
        )
        image = image_open(BytesIO(content))
        return image


class Company(CompanyFunctionsMetaClass):
    """Company class

    :param KFinanceApiClient kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param company_id: The S&P Global CIQ Company Id
    :type company_id: int
    """

    def __init__(self, kfinance_api_client: KFinanceApiClient, company_id: int):
        """Initialize the Company object

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param company_id: The S&P Global CIQ Company Id
        :type company_id: int
        """
        super().__init__()
        self.kfinance_api_client = kfinance_api_client
        self.company_id = company_id

    def __str__(self) -> str:
        """String representation for the company object"""
        return f"{type(self).__module__}.{type(self).__qualname__} of {self.company_id}"

    @cached_property
    def primary_security(self) -> Security:
        """Return the primary security item for the Company object

        :return: a Security object of the primary security of company_id
        :rtype: Security
        """
        primary_security_id = self.kfinance_api_client.fetch_primary_security(self.company_id)[
            "primary_security"
        ]
        self.primary_security = Security(
            kfinance_api_client=self.kfinance_api_client, security_id=primary_security_id
        )
        return self.primary_security

    @cached_property
    def securities(self) -> Securities:
        """Return the security items for the Company object

        :return: a Securities object containing the list of securities of company_id
        :rtype: Securities
        """
        security_ids = self.kfinance_api_client.fetch_securities(self.company_id)["securities"]
        self.securities = Securities(
            kfinance_api_client=self.kfinance_api_client, security_ids=security_ids
        )
        return self.securities

    @cached_property
    def latest_earnings_call(self) -> None:
        """Set and return the latest earnings call item for the object

        :raises NotImplementedError: This function is not yet implemented
        """
        raise NotImplementedError(
            "The latest earnings call property of company class not implemented yet"
        )

    @cached_property
    def info(self) -> dict:
        """Get the company info

        :return: a dict with containing: name, status, type, simple industry, number of employees, founding date, webpage, address, city, zip code, state, country, & iso_country
        :rtype: dict
        """
        self.info = self.kfinance_api_client.fetch_info(self.company_id)
        return self.info

    @property
    def name(self) -> str:
        """Get the company name

        :return: The company name
        :rtype: str
        """
        return self.info["name"]

    @property
    def status(self) -> str:
        """Get the company status

        :return: The company status
        :rtype: str
        """
        return self.info["status"]

    @property
    def type(self) -> str:
        """Get the type of company

        :return: The company type
        :rtype: str
        """
        return self.info["type"]

    @property
    def simple_industry(self) -> str:
        """Get the simple industry for the company

        :return: The company's simple_industry
        :rtype: str
        """
        return self.info["simple_industry"]

    @property
    def number_of_employees(self) -> str:
        """Get the number of employees the company has

        :return: how many employees the company has
        :rtype: str
        """
        return self.info["number_of_employees"]

    @property
    def founding_date(self) -> date:
        """Get the founding date for the company

        :return: founding date for the company
        :rtype: date
        """
        return datetime.strptime(self.info["founding_date"], "%Y-%m-%d").date()

    @property
    def webpage(self) -> str:
        """Get the webpage for the company

        :return: webpage for the company
        :rtype: str
        """
        return self.info["webpage"]

    @property
    def address(self) -> str:
        """Get the address of the company's HQ

        :return: address of the company's HQ
        :rtype: str
        """
        return self.info["address"]

    @property
    def city(self) -> str:
        """Get the city of the company's HQ

        :return: city of the company's HQ
        :rtype: str
        """
        return self.info["city"]

    @property
    def zip_code(self) -> str:
        """Get the zip code of the company's HQ

        :return: zip code of the company's HQ
        :rtype: str
        """
        return self.info["zip_code"]

    @property
    def state(self) -> str:
        """Get the state of the company's HQ

        :return: state of the company's HQ
        :rtype: str
        """
        return self.info["state"]

    @property
    def country(self) -> str:
        """Get the country of the company's HQ

        :return: country of the company's HQ
        :rtype: str
        """
        return self.info["country"]

    @property
    def iso_country(self) -> str:
        """Get the ISO code for the country of the company's HQ

        :return: iso code for the country of the company's HQ
        :rtype: str
        """
        return self.info["iso_country"]

    @cached_property
    def earnings_call_datetimes(self) -> list[datetime]:
        """Get the datetimes of the companies earnings calls

        :return: a list of datetimes for the companies earnings calls
        :rtype: list[datetime]
        """
        return [
            datetime.fromisoformat(earnings_call).replace(tzinfo=timezone.utc)
            for earnings_call in self.kfinance_api_client.fetch_earnings_dates(self.company_id)[
                "earnings"
            ]
        ]


class Security:
    """Security class

    :param kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param security_id: The S&P CIQ security id
    :type security_id: int
    """

    def __init__(
        self,
        kfinance_api_client: KFinanceApiClient,
        security_id: int,
    ):
        """Initialize the Security object.

        :param KFinanceApiClient kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param int security_id: The CIQ security id
        :type security_id: int
        """
        self.kfinance_api_client = kfinance_api_client
        self.security_id = security_id

    def __str__(self) -> str:
        """String representation for the security object"""
        return f"{type(self).__module__}.{type(self).__qualname__} of {self.security_id}"

    @cached_property
    def isin(self) -> str:
        """Get the ISIN for the object

        :return: The ISIN
        :rtype: str
        """
        return self.kfinance_api_client.fetch_isin(self.security_id)["isin"]

    @cached_property
    def cusip(self) -> str:
        """Get the CUSIP for the object

        :return: The CUSIP
        :rtype: str
        """
        return self.kfinance_api_client.fetch_cusip(self.security_id)["cusip"]

    @cached_property
    def primary_trading_item(self) -> TradingItem:
        """Return the primary trading item for the Security object

        :return: a TradingItem object of the primary trading item of security_id
        :rtype: TradingItem
        """
        primary_trading_item_id = self.kfinance_api_client.fetch_primary_trading_item(
            self.security_id
        )["primary_trading_item"]
        self.primary_trading_item = TradingItem(
            kfinance_api_client=self.kfinance_api_client, trading_item_id=primary_trading_item_id
        )
        return self.primary_trading_item

    @cached_property
    def trading_items(self) -> TradingItems:
        """Return the trading items for the Security object

        :return: a TradingItems object containing the list of trading items of security_id
        :rtype: TradingItems
        """
        trading_item_ids = self.kfinance_api_client.fetch_trading_items(self.security_id)[
            "trading_items"
        ]
        self.trading_items = TradingItems(
            kfinance_api_client=self.kfinance_api_client, trading_item_ids=trading_item_ids
        )
        return self.trading_items


class Ticker(DelegatedCompanyFunctionsMetaClass):
    """Base Ticker class for accessing data on company

    :param kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param exchange_code: The exchange code identifying which exchange the ticker is on
    :type exchange_code: str, optional
    """

    def __init__(
        self,
        kfinance_api_client: KFinanceApiClient,
        identifier: Optional[str] = None,
        exchange_code: Optional[str] = None,
        company_id: Optional[int] = None,
        security_id: Optional[int] = None,
        trading_item_id: Optional[int] = None,
    ) -> None:
        """Initialize the Ticker object. [identifier] can be a ticker, ISIN, or CUSIP. Identifier is prioritized over identification triple (company_id, security_id, & trading_item_id)

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param identifier: The ticker symbol, ISIN, or CUSIP, default None
        :type identifier: str, optional
        :param exchange_code: The exchange code identifying which exchange the ticker is on. It is only needed if symbol is passed in and default None
        :type exchange_code: str, optional
        :param company_id: The S&P Global CIQ Company Id, defaults None
        :type company_id: int, optional
        :param security_id: The S&P Global CIQ Security Id, default None
        :type security_id: int, optional
        :param trading_item_id: The S&P Global CIQ Trading Item Id, default None
        :type trading_item_id: int, optional
        """
        super().__init__()
        self._identifier = identifier
        self.kfinance_api_client = kfinance_api_client
        self._ticker: Optional[str] = None
        self.exchange_code: Optional[str] = exchange_code
        self._isin: Optional[str] = None
        self._cusip: Optional[str] = None
        self._company_id: Optional[int] = None
        self._security_id: Optional[int] = None
        self._trading_item_id: Optional[int] = None
        if self._identifier is not None:
            if re.match("^[a-zA-Z]{2}[a-zA-Z0-9]{9}[0-9]{1}$", self._identifier):  # Regex for ISIN
                self._isin = self._identifier
            elif re.match("^[a-zA-Z0-9]{9}$", self._identifier):  # Regex for CUSIP
                self._cusip = self._identifier
            else:
                self._ticker = self._identifier
        elif company_id is not None and security_id is not None and trading_item_id is not None:
            self._company_id = company_id
            self._security_id = security_id
            self._trading_item_id = trading_item_id
        else:
            raise RuntimeError(
                "Neither an identifier nor an identification triple (company id, security id, & trading item id) were passed in"
            )

    def __str__(self) -> str:
        """String representation for the ticker object"""
        str_attributes = []
        if self._ticker:
            str_attributes.append(
                f"{self.exchange_code + ':' if self.exchange_code else ''}{self.ticker}"
            )
        if self._isin:
            str_attributes.append(self._isin)
        if self._cusip:
            str_attributes.append(str(self._cusip))
        if self._company_id and self._security_id and self._trading_item_id:
            str_attributes.append(
                f"identification triple ({self._company_id}/{self._security_id}/{self._trading_item_id})"
            )

        return f"{type(self).__module__}.{type(self).__qualname__} of {', '.join(str_attributes)}"

    def set_identification_triple(self) -> None:
        """Get & set company_id, security_id, & trading_item_id for ticker with an exchange"""
        if self._identifier is None:
            raise RuntimeError(
                "Ticker.set_identification_triple was called with a identifier set to None"
            )
        else:
            id_triple = self.kfinance_api_client.fetch_id_triple(
                self._identifier, self.exchange_code
            )
            self.company_id = id_triple["company_id"]
            self.security_id = id_triple["security_id"]
            self.trading_item_id = id_triple["trading_item_id"]

    def set_company_id(self) -> int:
        """Set the company id for the object

        :return: the CIQ company id
        :rtype: int
        """
        self.set_identification_triple()
        return self.company_id

    def set_security_id(self) -> int:
        """Set the security id for the object

        :return: the CIQ security id
        :rtype: int
        """
        self.set_identification_triple()
        return self.security_id

    def set_trading_item_id(self) -> int:
        """Set the trading item id for the object

        :return: the CIQ trading item id
        :rtype: int
        """
        self.set_identification_triple()
        return self.trading_item_id

    @cached_property
    def company_id(self) -> int:
        """Get the company id for the object

        :return: the CIQ company id
        :rtype: int
        """
        if self._company_id:
            return self._company_id
        return self.set_company_id()

    @cached_property
    def security_id(self) -> int:
        """Get the CIQ security id for the object

        :return: the CIQ security id
        :rtype: int
        """
        if self._security_id:
            return self._security_id
        return self.set_security_id()

    @cached_property
    def trading_item_id(self) -> int:
        """Get the CIQ trading item id for the object

        :return: the CIQ trading item id
        :rtype: int
        """
        if self._trading_item_id:
            return self._trading_item_id
        return self.set_trading_item_id()

    @cached_property
    def primary_security(self) -> Security:
        """Set and return the primary security for the object

        :return: The primary security as a Security object
        :rtype: Security
        """

        self.primary_security = Security(
            kfinance_api_client=self.kfinance_api_client, security_id=self.security_id
        )
        return self.primary_security

    @cached_property
    def company(self) -> Company:
        """Set and return the company for the object

        :return: The company returned as Company object
        :rtype: Company
        """
        self.company = Company(
            kfinance_api_client=self.kfinance_api_client, company_id=self.company_id
        )
        return self.company

    @cached_property
    def primary_trading_item(self) -> TradingItem:
        """Set and return the trading item for the object

        :return: The trading item returned as TradingItem object
        :rtype: TradingItem
        """
        self.primary_trading_item = TradingItem(
            kfinance_api_client=self.kfinance_api_client, trading_item_id=self.trading_item_id
        )
        return self.primary_trading_item

    @cached_property
    def isin(self) -> str:
        """Get the ISIN for the object

        :return: The ISIN
        :rtype: str
        """
        if self._isin:
            return self._isin
        isin = self.primary_security.isin
        self._isin = isin
        return isin

    @cached_property
    def cusip(self) -> str:
        """Get the CUSIP for the object

        :return: The CUSIP
        :rtype: str
        """
        if self._cusip:
            return self._cusip
        cusip = self.primary_security.cusip
        self._cusip = cusip
        return cusip

    @cached_property
    def info(self) -> dict:
        """Get the company info for the ticker

        :return: a dict with containing: name, status, type, simple industry, number of employees, founding date, webpage, address, city, zip code, state, country, & iso_country
        :rtype: dict
        """
        return self.company.info

    @property
    def name(self) -> str:
        """Get the company name

        :return: The company name
        :rtype: str
        """
        return self.company.name

    @property
    def status(self) -> str:
        """Get the company status

        :return: The company status
        :rtype: str
        """
        return self.company.status

    @property
    def type(self) -> str:
        """Get the type of company

        :return: The company type
        :rtype: str
        """
        return self.company.type

    @property
    def simple_industry(self) -> str:
        """Get the simple industry for the company

        :return: The company's simple_industry
        :rtype: str
        """
        return self.company.simple_industry

    @property
    def number_of_employees(self) -> str:
        """Get the number of employees the company has

        :return: how many employees the company has
        :rtype: str
        """
        return self.company.number_of_employees

    @property
    def founding_date(self) -> date:
        """Get the founding date for the company

        :return: founding date for the company
        :rtype: date
        """
        return self.company.founding_date

    @property
    def webpage(self) -> str:
        """Get the webpage for the company

        :return: webpage for the company
        :rtype: str
        """
        return self.company.webpage

    @property
    def address(self) -> str:
        """Get the address of the company's HQ

        :return: address of the company's HQ
        :rtype: str
        """
        return self.company.address

    @property
    def city(self) -> str:
        """Get the city of the company's HQ

        :return: city of the company's HQ
        :rtype: str
        """
        return self.company.city

    @property
    def zip_code(self) -> str:
        """Get the zip code of the company's HQ

        :return: zip code of the company's HQ
        :rtype: str
        """
        return self.company.zip_code

    @property
    def state(self) -> str:
        """Get the state of the company's HQ

        :return: state of the company's HQ
        :rtype: str
        """
        return self.company.state

    @property
    def country(self) -> str:
        """Get the country of the company's HQ

        :return: country of the company's HQ
        :rtype: str
        """
        return self.company.country

    @property
    def iso_country(self) -> str:
        """Get the ISO code for the country of the company's HQ

        :return: iso code for the country of the company's HQ
        :rtype: str
        """
        return self.company.iso_country

    @cached_property
    def earnings_call_datetimes(self) -> list[datetime]:
        """Get the datetimes of the companies earnings calls

        :return: a list of datetimes for the companies earnings calls
        :rtype: list[datetime]
        """
        return self.company.earnings_call_datetimes

    @cached_property
    def history_metadata(self) -> HistoryMetadata:
        """Get information about exchange and quotation

        :return: A dict containing data about the currency, symbol, exchange, type of instrument, and the first trading date
        :rtype: HistoryMetadata
        """
        metadata = self.primary_trading_item.history_metadata
        if self.exchange_code is None:
            self.exchange_code = metadata["exchange_name"]
        if self._ticker is None:
            self._ticker = metadata["symbol"]
        return metadata

    @cached_property
    def ticker(self) -> str:
        """Get the ticker if it isn't available from initialization"""
        if self._ticker is not None:
            return self._ticker
        return self.history_metadata["symbol"]

    def history(
        self,
        periodicity: str = "day",
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves the historical price data for a given asset over a specified date range.

        :param periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :type periodicity: str
        :param adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :type adjusted: bool, optional
        :param start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A pd.DataFrame containing historical price data with columns corresponding to the specified periodicity, with Date as the index, and columns "open", "high", "low", "close", "volume" in type decimal. The Date index is a string that depends on the periodicity. If periodicity="day", the Date index is the day in format "YYYY-MM-DD", eg "2024-05-13" If periodicity="week", the Date index is the week number of the year in format "YYYY Week ##", eg "2024 Week 2" If periodicity="month", the Date index is the month name of the year in format "<Month> YYYY", eg "January 2024". If periodicity="year", the Date index is the year in format "YYYY", eg "2024".
        :rtype: pd.DataFrame
        """
        return self.primary_trading_item.history(
            periodicity,
            adjusted,
            start_date,
            end_date,
        )

    def price_chart(
        self,
        periodicity: str = "day",
        adjusted: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Image:
        """Get the price chart.

        :param periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :type periodicity: str
        :param adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :type adjusted: bool, optional
        :param start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: An image showing the price chart of the trading item
        :rtype: Image
        """
        return self.primary_trading_item.price_chart(periodicity, adjusted, start_date, end_date)


class BusinessRelationships(NamedTuple):
    """Business relationships object that represents the current and previous companies of a given Company object.

    :param current: A Companies set that represents the current company_ids.
    :param previous: A Companies set that represents the previous company_ids.
    """

    current: Companies
    previous: Companies

    def __str__(self) -> str:
        """String representation for the BusinessRelationships object"""
        dictionary = {
            "current": [company.company_id for company in self.current],
            "previous": [company.company_id for company in self.previous],
        }
        return f"{type(self).__module__}.{type(self).__qualname__} of {str(dictionary)}"


@add_methods_of_singular_class_to_iterable_class(Company)
class Companies(set):
    """Base class for representing a set of Companies"""

    def __init__(self, kfinance_api_client: KFinanceApiClient, company_ids: Iterable[int]) -> None:
        """Initialize the Companies object

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param company_ids: An iterable of S&P CIQ Company ids
        :type company_ids: Iterable[int]
        """
        self.kfinance_api_client = kfinance_api_client
        super().__init__(Company(kfinance_api_client, company_id) for company_id in company_ids)


@add_methods_of_singular_class_to_iterable_class(Security)
class Securities(set):
    """Base class for representing a set of Securities"""

    def __init__(self, kfinance_api_client: KFinanceApiClient, security_ids: Iterable[int]) -> None:
        """Initialize the Securities

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param security_ids: An iterable of S&P CIQ Security ids
        :type security_ids: Iterable[int]
        """
        super().__init__(Security(kfinance_api_client, security_id) for security_id in security_ids)


@add_methods_of_singular_class_to_iterable_class(TradingItem)
class TradingItems(set):
    """Base class for representing a set of Trading Items"""

    def __init__(
        self, kfinance_api_client: KFinanceApiClient, trading_item_ids: Iterable[int]
    ) -> None:
        """Initialize the Trading Items

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param company_ids: An iterable of S&P CIQ Company ids
        :type company_ids: Iterable[int]
        """
        self.kfinance_api_client = kfinance_api_client
        super().__init__(
            TradingItem(kfinance_api_client, trading_item_id)
            for trading_item_id in trading_item_ids
        )


@add_methods_of_singular_class_to_iterable_class(Ticker)
class Tickers(set):
    """Base class for representing a set of Tickers"""

    def __init__(
        self,
        kfinance_api_client: KFinanceApiClient,
        id_triples: Iterable[IdentificationTriple],
    ) -> None:
        """Initialize the Ticker Set

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param id_triples: An Iterable of IdentificationTriples that will become the ticker objects making up the tickers object
        :type id_triples: Iterable[IdentificationTriple]
        """
        self.kfinance_api_client = kfinance_api_client
        super().__init__(
            Ticker(
                kfinance_api_client=kfinance_api_client,
                company_id=id_triple["company_id"],
                security_id=id_triple["security_id"],
                trading_item_id=id_triple["trading_item_id"],
            )
            for id_triple in id_triples
        )

    def companies(self) -> Companies:
        """Build a group of company objects from the group of tickers

        :return: The Companies corresponding to the Tickers
        :rtype: Companies
        """
        return Companies(
            self.kfinance_api_client, (ticker.company_id for ticker in self.__iter__())
        )

    def securities(self) -> Securities:
        """Build a group of security objects from the group of tickers

        :return: The Securities corresponding to the Tickers
        :rtype: Securities
        """
        return Securities(
            self.kfinance_api_client, (ticker.security_id for ticker in self.__iter__())
        )

    def trading_items(self) -> TradingItems:
        """Build a group of trading item objects from the group of ticker

        :return: The TradingItems corresponding to the Tickers
        :rtype: TradingItems
        """
        return TradingItems(
            self.kfinance_api_client, (ticker.trading_item_id for ticker in self.__iter__())
        )


class Client:
    """Client class with LLM tools and a pre-credentialed Ticker object

    :param tools: A dictionary mapping function names to functions, where each function is an llm tool with the Client already passed in if applicable
    :type tools: dict[str, Callable]
    :param anthropic_tool_descriptions: A list of dictionaries, where each dictionary is an Anthropic tool definition
    :type anthropic_tool_descriptions: list[dict]
    :param gemini_tool_descriptions: A dictionary mapping "function_declarations" to a list of dictionaries, where each dictionary is a Gemini tool definition
    :type gemini_tool_descriptions: dict[list[dict]]
    :param openai_tool_descriptions: A list of dictionaries, where each dictionary is an OpenAI tool definition
    :type openai_tool_descriptions: list[dict]
    """

    prompt = PROMPT

    def __init__(
        self,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        private_key: Optional[str] = None,
        thread_pool: Optional[ThreadPoolExecutor] = None,
        api_host: str = DEFAULT_API_HOST,
        api_version: int = DEFAULT_API_VERSION,
        okta_host: str = DEFAULT_OKTA_HOST,
        okta_auth_server: str = DEFAULT_OKTA_AUTH_SERVER,
    ):
        """Initialization of the client.

        :param refresh_token: users refresh token
        :type refresh_token: str, Optional
        :param client_id: users client id will be provided by support@kensho.com
        :type client_id: str, Optional
        :param private_key: users private key that corresponds to the registered public sent to support@kensho.com
        :type private_key: str, Optional
        :param thread_pool: the thread pool used to execute batch requests. The number of concurrent requests is
        capped at 10. If no thread pool is provided, a thread pool with 10 max workers will be created when batch
        requests are made.
        :type thread_pool: ThreadPoolExecutor, Optional
        :param api_host: the api host URL
        :type api_host: str
        :param api_version: the api version number
        :type api_version: int
        :param okta_host: the okta host URL
        :type okta_host: str
        :param okta_auth_server: the okta route for authentication
        :type okta_auth_server: str
        """

        # method 1 refresh token
        if refresh_token is not None:
            self.kfinance_api_client = KFinanceApiClient(
                refresh_token=refresh_token,
                api_host=api_host,
                api_version=api_version,
                okta_host=okta_host,
                thread_pool=thread_pool,
            )
        # method 2 keypair
        elif client_id is not None and private_key is not None:
            self.kfinance_api_client = KFinanceApiClient(
                client_id=client_id,
                private_key=private_key,
                api_host=api_host,
                api_version=api_version,
                okta_host=okta_host,
                okta_auth_server=okta_auth_server,
                thread_pool=thread_pool,
            )
        # method 3 automatic login getting a refresh token
        else:
            server_thread = ServerThread()
            stdout.write("Please login with your credentials.\n")
            server_thread.start()
            webbrowser.open(
                urljoin(
                    api_host if api_host else DEFAULT_API_HOST,
                    f"automated_login?port={server_thread.server_port}",
                )
            )
            server_thread.join()
            self.kfinance_api_client = KFinanceApiClient(
                refresh_token=server_thread.refresh_token,
                api_host=api_host,
                api_version=api_version,
                okta_host=okta_host,
                thread_pool=thread_pool,
            )
            stdout.write("Login credentials received.\n")

        self._tools: list[KfinanceTool] | None = None

    @property
    def langchain_tools(self) -> list["KfinanceTool"]:
        """Return a list of all Kfinance tools for tool calling."""
        if self._tools is None:
            from kfinance.tool_calling import ALL_TOOLS

            self._tools = [t(kfinance_client=self) for t in ALL_TOOLS]  # type: ignore[call-arg]
        return self._tools

    @property
    def tools(self) -> dict[str, Callable]:
        """Return a mapping of tool calling function names to the corresponding functions.

        `tools` is intended for running without langchain. When running with langchain,
        use `langchain_tools`.
        """
        return {t.name: t.run_without_langchain for t in self.langchain_tools}

    @property
    def anthropic_tool_descriptions(self) -> list[dict[str, Any]]:
        """Return tool descriptions for anthropic"""

        anthropic_tool_descriptions = []

        for tool in self.langchain_tools:
            # Copied from https://python.langchain.com/api_reference/_modules/langchain_anthropic/chat_models.html#convert_to_anthropic_tool
            # to avoid adding a langchain-anthropic dependency.
            oai_formatted = convert_to_openai_tool(tool)["function"]
            anthropic_tool_descriptions.append(
                dict(
                    name=oai_formatted["name"],
                    description=oai_formatted["description"],
                    input_schema=oai_formatted["parameters"],
                )
            )

        return anthropic_tool_descriptions

    @property
    def gemini_tool_descriptions(self) -> list[dict[str, Any]]:
        """Return tool descriptions for gemini"""
        gemini_tool_descriptions = [
            convert_to_openai_tool(t)["function"] for t in self.langchain_tools
        ]
        return [{"function_declarations": gemini_tool_descriptions}]

    @property
    def openai_tool_descriptions(self) -> list[dict[str, Any]]:
        """Return tool descriptions for gemini"""
        openai_tool_descriptions = [convert_to_openai_tool(t) for t in self.langchain_tools]
        return openai_tool_descriptions

    @property
    def access_token(self) -> str:
        """Returns the client access token.

        :return: A valid access token for use in API
        :rtype: str
        """
        return self.kfinance_api_client.access_token

    def ticker(
        self,
        identifier: int | str,
        exchange_code: Optional[str] = None,
        function_called: Optional[bool] = False,
    ) -> Ticker:
        """Generate Ticker object from [identifier] that is a ticker, ISIN, or CUSIP.

        :param  identifier: the ticker symbol, ISIN, or CUSIP
        :type identifier: str
        :param exchange_code: The code representing the equity exchange the ticker is listed on.
        :type exchange_code: str, optional
        :param function_called: Flag for use in signaling function calling
        :type function_called: bool, optional
        :return: Ticker object from that corresponds to the identifier
        :rtype: Ticker
        """
        if function_called:
            self.kfinance_api_client.user_agent_source = "tool_calling"
        return Ticker(self.kfinance_api_client, str(identifier), exchange_code)

    def tickers(
        self,
        country_iso_code: Optional[str] = None,
        state_iso_code: Optional[str] = None,
        simple_industry: Optional[str] = None,
        exchange_code: Optional[str] = None,
    ) -> Tickers:
        """Generate tickers object representing the collection of Tickers that meet all the supplied parameters

        One of country_iso_code, simple_industry, or exchange_code must be supplied. A parameter set to None is not used to filter on

        :param country_iso_code: The ISO 3166-1 Alpha-2 or Alpha-3 code that represent the primary country the firm is based in. It default None
        :type country_iso_code: str, optional
        :param state_iso_code: The ISO 3166-2 Alpha-2 code that represents the primary subdivision of the country the firm the based in. Not all ISO 3166-2 codes are supported as S&P doesn't maintain the full list but a feature request for the full list is submitted to S&P product. Requires country_iso_code also to have a value other then None. It default None
        :type state_iso_code: str, optional
        :param simple_industry: The S&P CIQ Simple Industry defined in ciqSimpleIndustry in XPF. It default None
        :type simple_industry: str, optional
        :param exchange_code: The exchange code for the primary equity listing exchange of the firm. It default None
        :type exchange_code: str, optional
        :return: A tickers object that is the group of Ticker objects meeting all the supplied parameters
        :rtype: Tickers
        """
        return Tickers(
            kfinance_api_client=self.kfinance_api_client,
            id_triples=self.kfinance_api_client.fetch_ticker_combined(
                country_iso_code=country_iso_code,
                state_iso_code=state_iso_code,
                simple_industry=simple_industry,
                exchange_code=exchange_code,
            )["tickers"],
        )

    def company(self, company_id: int) -> Company:
        """Generate the Company object from company_id

        :param company_id: CIQ company id
        :type company_id: int
        :return: The Company specified by the the company id
        :rtype: Company
        """
        return Company(kfinance_api_client=self.kfinance_api_client, company_id=company_id)

    def security(self, security_id: int) -> Security:
        """Generate Security object from security_id

        :param security_id: CIQ security id
        :type security_id: int
        :return: The Security specified by the the security id
        :rtype: Security
        """
        return Security(kfinance_api_client=self.kfinance_api_client, security_id=security_id)

    def trading_item(self, trading_item_id: int) -> TradingItem:
        """Generate TradingItem object from trading_item_id

        :param trading_item_id: CIQ trading item id
        :type trading_item_id: int
        :return: The trading item specified by the the trading item id
        :rtype: TradingItem
        """
        return TradingItem(
            kfinance_api_client=self.kfinance_api_client, trading_item_id=trading_item_id
        )

    @staticmethod
    def get_latest(use_local_timezone: bool = True) -> LatestPeriods:
        """Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date.

        :param use_local_timezone: whether to use the local timezone of the user
        :type use_local_timezone: bool
        :return: A dict in the form of {"annual": {"latest_year": int}, "quarterly": {"latest_quarter": int, "latest_year": int}, "now": {"current_year": int, "current_quarter": int, "current_month": int, "current_date": str of Y-m-d}}
        :rtype: Latest
        """

        datetime_now = datetime.now() if use_local_timezone else datetime.now(timezone.utc)
        current_year = datetime_now.year
        current_qtr = (datetime_now.month - 1) // 3 + 1

        # Quarterly data. Get most recent year and quarter
        if current_qtr == 1:
            most_recent_year_qtrly = current_year - 1
            most_recent_qtr = 4
        else:
            most_recent_year_qtrly = current_year
            most_recent_qtr = current_qtr - 1

        # Annual data. Get most recent year
        most_recent_year_annual = current_year - 1

        current_month = datetime_now.month
        latest: LatestPeriods = {
            "annual": {"latest_year": most_recent_year_annual},
            "quarterly": {"latest_quarter": most_recent_qtr, "latest_year": most_recent_year_qtrly},
            "now": {
                "current_year": current_year,
                "current_quarter": current_qtr,
                "current_month": current_month,
                "current_date": datetime_now.date().isoformat(),
            },
        }
        return latest

    @staticmethod
    def get_n_quarters_ago(n: int) -> YearAndQuarter:
        """Get the year and quarter corresponding to [n] quarters before the current quarter

        :param int n: the number of quarters before the current quarter
        :return: A dict in the form of {"year": int, "quarter": int}
        :rtype: YearAndQuarter
        """

        datetime_now = datetime.now()
        current_qtr = (datetime_now.month - 1) // 3 + 1
        total_quarters_completed = datetime_now.year * 4 + current_qtr - 1
        total_quarters_completed_n_quarters_ago = total_quarters_completed - n

        year_n_quarters_ago = total_quarters_completed_n_quarters_ago // 4
        quarter_n_quarters_ago = total_quarters_completed_n_quarters_ago % 4 + 1

        year_quarter_n_quarters_ago: YearAndQuarter = {
            "year": year_n_quarters_ago,
            "quarter": quarter_n_quarters_ago,
        }

        return year_quarter_n_quarters_ago
