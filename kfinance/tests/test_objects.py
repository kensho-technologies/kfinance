from datetime import datetime, timezone
from io import BytesIO
import re
from typing import Optional
from unittest import TestCase

import numpy as np
import pandas as pd
from PIL.Image import open as image_open

from kfinance.kfinance import Company, Security, Ticker, TradingItem


msft_company_id = "21835"
msft_security_id = "2630412"
msft_isin = "US5949181045"
msft_cusip = "594918104"
msft_trading_item_id = "2630413"


MOCK_TRADING_ITEM_DB = {
    msft_trading_item_id: {
        "metadata": {
            "currency": "USD",
            "symbol": "MSFT",
            "exchange_name": "NasdaqGS",
            "instrument_type": "Equity",
            "first_trade_date": "1986-03-13",
        },
        "price_chart": {
            "2020-01-01": {
                "2021-01-01": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03"
            }
        },
    }
}


MOCK_COMPANY_DB = {
    msft_company_id: {
        "info": {
            "name": "Microsoft Corporation",
            "status": "Operating",
            "type": "Public Company",
            "simple_industry": "Software",
            "number_of_employees": "228000.0000",
            "founding_date": "1975-01-01",
            "webpage": "www.microsoft.com",
            "address": "One Microsoft Way",
            "city": "Redmond",
            "zip_code": "98052-6399",
            "state": "Washington",
            "country": "United States",
            "iso_country": "USA",
        },
        "earnings_call_dates": {"earnings": ["2004-07-22T21:30:00"]},
        "statements": {
            "income_statement": {
                "statements": {
                    "2019": {
                        "Revenues": "125843000000.000000",
                        "Total Revenues": "125843000000.000000",
                    }
                }
            }
        },
        "line_items": {
            "revenue": {
                "line_item": {
                    "2019": "125843000000.000000",
                    "2020": "143015000000.000000",
                    "2021": "168088000000.000000",
                    "2022": "198270000000.000000",
                    "2023": "211915000000.000000",
                }
            }
        },
    }
}


MOCK_SECURITY_DB = {msft_security_id: {"isin": msft_isin, "cusip": msft_cusip}}


MOCK_TICKER_DB = {
    "MSFT": {
        "company_id": msft_company_id,
        "security_id": msft_security_id,
        "trading_item_id": msft_trading_item_id,
    }
}

MOCK_ISIN_DB = {
    msft_isin: {
        "company_id": msft_company_id,
        "security_id": msft_security_id,
        "trading_item_id": msft_trading_item_id,
    }
}

MOCK_CUSIP_DB = {
    msft_cusip: {
        "company_id": msft_company_id,
        "security_id": msft_security_id,
        "trading_item_id": msft_trading_item_id,
    }
}


class MockKFinanceApiClient:
    def __init__(self):
        """Create a mock kfinance api client"""
        pass

    def fetch_id_triple(self, identifier: int | str, exchange_code: Optional[str] = None) -> dict:
        """Get the ID triple from ticker."""
        if re.match("^[a-zA-Z]{2}[a-zA-Z0-9]{9}[0-9]{1}$", str(identifier)):
            return MOCK_ISIN_DB[identifier]
        elif re.match("^[a-zA-Z0-9]{9}$", str(identifier)):
            return MOCK_CUSIP_DB[identifier]
        else:
            return MOCK_TICKER_DB[identifier]

    def fetch_isin(self, security_id: int) -> dict:
        """Get the ISIN."""
        return {"isin": MOCK_SECURITY_DB[security_id]["isin"]}

    def fetch_cusip(self, security_id: int) -> dict:
        """Get the CUSIP."""
        return {"cusip": MOCK_SECURITY_DB[security_id]["cusip"]}

    def fetch_history_metadata(self, trading_item_id):
        """Get history metadata"""
        return MOCK_TRADING_ITEM_DB[trading_item_id]["metadata"].copy()

    def fetch_price_chart(
        self, trading_item_id, is_adjusted, start_date, end_date, periodicity
    ) -> bytes:
        """Get price chart"""
        return MOCK_TRADING_ITEM_DB[trading_item_id]["price_chart"][start_date][end_date]

    def fetch_info(self, company_id: int) -> dict:
        """Get info"""
        return MOCK_COMPANY_DB[company_id]["info"]

    def fetch_earnings_dates(self, company_id: int):
        """Get the earnings dates"""
        return MOCK_COMPANY_DB[company_id]["earnings_call_dates"]

    def fetch_statement(
        self,
        company_id,
        statement_type,
        period_type,
        start_year,
        end_year,
        start_quarter,
        end_quarter,
    ):
        """Get a statement"""
        return MOCK_COMPANY_DB[company_id]["statements"][statement_type]

    def fetch_line_item(
        self, company_id, line_item, period_type, start_year, end_year, start_quarter, end_quarter
    ):
        """Get a statement"""
        return MOCK_COMPANY_DB[company_id]["line_items"][line_item]

    def fetch_market_caps_tevs_and_shares_outstanding(
        self,
        company_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        return {
            "market_caps": [
                {
                    "date": "2025-01-01",
                    "market_cap": "3133802247084.000000",
                    "tev": "3152211247084.000000",
                    "shares_outstanding": 7434880776,
                },
                {
                    "date": "2025-01-02",
                    "market_cap": "3112092395218.000000",
                    "tev": "3130501395218.000000",
                    "shares_outstanding": 7434880776,
                },
            ]
        }


class TestTradingItem(TestCase):
    def setUp(self):
        """setup tests"""
        self.kfinance_api_client = MockKFinanceApiClient()
        self.msft_trading_item_from_id = TradingItem(self.kfinance_api_client, msft_trading_item_id)
        self.msft_trading_item_from_ticker = TradingItem.from_ticker(
            self.kfinance_api_client, "MSFT"
        )

    def test_trading_item_id(self) -> None:
        """test trading item id"""
        expected_trading_item_id = MOCK_TICKER_DB["MSFT"]["trading_item_id"]
        trading_item_id = self.msft_trading_item_from_id.trading_item_id
        self.assertEqual(expected_trading_item_id, trading_item_id)

        trading_item_id = self.msft_trading_item_from_ticker.trading_item_id
        self.assertEqual(expected_trading_item_id, trading_item_id)

    def test_history_metadata(self) -> None:
        """test history metadata"""
        expected_history_metadata = MOCK_TRADING_ITEM_DB[msft_trading_item_id]["metadata"].copy()
        expected_history_metadata["first_trade_date"] = datetime.strptime(
            expected_history_metadata["first_trade_date"], "%Y-%m-%d"
        ).date()
        expected_exchange_code = "NasdaqGS"
        history_metadata = self.msft_trading_item_from_id.history_metadata
        self.assertEqual(expected_history_metadata, history_metadata)
        self.assertEqual(expected_exchange_code, self.msft_trading_item_from_id.exchange_code)

        history_metadata = self.msft_trading_item_from_ticker.history_metadata
        self.assertEqual(expected_history_metadata, history_metadata)
        self.assertEqual(expected_exchange_code, self.msft_trading_item_from_ticker.exchange_code)

    def test_price_chart(self):
        """test price chart"""
        expected_price_chart = image_open(
            BytesIO(
                MOCK_TRADING_ITEM_DB[msft_trading_item_id]["price_chart"]["2020-01-01"][
                    "2021-01-01"
                ]
            )
        )
        price_chart = self.msft_trading_item_from_id.price_chart(
            start_date="2020-01-01", end_date="2021-01-01"
        )
        self.assertEqual(expected_price_chart, price_chart)

        price_chart = self.msft_trading_item_from_ticker.price_chart(
            start_date="2020-01-01", end_date="2021-01-01"
        )
        self.assertEqual(expected_price_chart, price_chart)


class TestCompany(TestCase):
    def setUp(self):
        """setup tests"""
        self.kfinance_api_client = MockKFinanceApiClient()
        self.msft_company = Company(self.kfinance_api_client, msft_company_id)

    def test_company_id(self) -> None:
        """test company id"""
        expected_company_id = msft_company_id
        company_id = self.msft_company.company_id
        self.assertEqual(expected_company_id, company_id)

    def test_info(self) -> None:
        """test info"""
        expected_info = MOCK_COMPANY_DB[msft_company_id]["info"]
        info = self.msft_company.info
        self.assertEqual(expected_info, info)

    def test_name(self) -> None:
        """test name"""
        expected_name = MOCK_COMPANY_DB[msft_company_id]["info"]["name"]
        name = self.msft_company.name
        self.assertEqual(expected_name, name)

    def test_founding_date(self) -> None:
        """test founding date"""
        expected_founding_date = datetime.strptime(
            MOCK_COMPANY_DB[msft_company_id]["info"]["founding_date"], "%Y-%m-%d"
        ).date()
        founding_date = self.msft_company.founding_date
        self.assertEqual(expected_founding_date, founding_date)

    def test_earnings_call_datetimes(self) -> None:
        """test earnings call datetimes"""
        expected_earnings_call_datetimes = [
            datetime.fromisoformat(
                MOCK_COMPANY_DB[msft_company_id]["earnings_call_dates"]["earnings"][0]
            ).replace(tzinfo=timezone.utc)
        ]
        earnings_call_datetimes = self.msft_company.earnings_call_datetimes
        self.assertEqual(expected_earnings_call_datetimes, earnings_call_datetimes)

    def test_income_statement(self) -> None:
        """test income statement"""
        expected_income_statement = (
            pd.DataFrame(
                MOCK_COMPANY_DB[msft_company_id]["statements"]["income_statement"]["statements"]
            )
            .apply(pd.to_numeric)
            .replace(np.nan, None)
        )
        income_statement = self.msft_company.income_statement()
        pd.testing.assert_frame_equal(expected_income_statement, income_statement)

    def test_revenue(self) -> None:
        """test revenue"""
        expected_revenue = (
            pd.DataFrame(MOCK_COMPANY_DB[msft_company_id]["line_items"]["revenue"])
            .transpose()
            .apply(pd.to_numeric)
            .replace(np.nan, None)
            .set_index(pd.Index(["revenue"]))
        )
        revenue = self.msft_company.revenue()
        pd.testing.assert_frame_equal(expected_revenue, revenue)


class TestSecurity(TestCase):
    def setUp(self):
        """setup tests"""
        self.kfinance_api_client = MockKFinanceApiClient()
        self.msft_security = Security(self.kfinance_api_client, msft_security_id)

    def test_security_id(self) -> None:
        """test security id"""
        expected_security_id = msft_security_id
        security_id = self.msft_security.security_id
        self.assertEqual(expected_security_id, security_id)

    def test_isin(self) -> None:
        """test isin"""
        expected_isin = MOCK_SECURITY_DB[self.msft_security.security_id]["isin"]
        isin = self.msft_security.isin
        self.assertEqual(expected_isin, isin)


class TestTicker(TestCase):
    def setUp(self):
        """setup tests"""
        self.kfinance_api_client = MockKFinanceApiClient()
        self.msft_ticker_from_ticker = Ticker(self.kfinance_api_client, "MSFT")
        self.msft_ticker_from_isin = Ticker(self.kfinance_api_client, msft_isin)
        self.msft_ticker_from_cusip = Ticker(self.kfinance_api_client, msft_cusip)
        self.msft_ticker_from_id_triple = Ticker(
            self.kfinance_api_client,
            company_id=msft_company_id,
            security_id=msft_security_id,
            trading_item_id=msft_trading_item_id,
        )

    def test_company_id(self) -> None:
        """test company id"""
        expected_company_id = MOCK_TICKER_DB[self.msft_ticker_from_ticker.ticker]["company_id"]
        company_id = self.msft_ticker_from_ticker.company_id
        self.assertEqual(expected_company_id, company_id)

        company_id = self.msft_ticker_from_isin.company_id
        self.assertEqual(expected_company_id, company_id)

        company_id = self.msft_ticker_from_cusip.company_id
        self.assertEqual(expected_company_id, company_id)

        company_id = self.msft_ticker_from_id_triple.company_id
        self.assertEqual(expected_company_id, company_id)

    def test_security_id(self) -> None:
        """test security id"""
        expected_security_id = MOCK_TICKER_DB[self.msft_ticker_from_ticker.ticker]["security_id"]
        security_id = self.msft_ticker_from_ticker.security_id
        self.assertEqual(expected_security_id, security_id)

        security_id = self.msft_ticker_from_isin.security_id
        self.assertEqual(expected_security_id, security_id)

        security_id = self.msft_ticker_from_cusip.security_id
        self.assertEqual(expected_security_id, security_id)

        security_id = self.msft_ticker_from_id_triple.security_id
        self.assertEqual(expected_security_id, security_id)

    def test_trading_item_id(self) -> None:
        """test trading item id"""
        expected_trading_item_id = MOCK_TICKER_DB[self.msft_ticker_from_ticker.ticker][
            "trading_item_id"
        ]
        trading_item_id = self.msft_ticker_from_ticker.trading_item_id
        self.assertEqual(expected_trading_item_id, trading_item_id)

        trading_item_id = self.msft_ticker_from_isin.trading_item_id
        self.assertEqual(expected_trading_item_id, trading_item_id)

        trading_item_id = self.msft_ticker_from_cusip.trading_item_id
        self.assertEqual(expected_trading_item_id, trading_item_id)

        trading_item_id = self.msft_ticker_from_id_triple.trading_item_id
        self.assertEqual(expected_trading_item_id, trading_item_id)

    def test_cusip(self) -> None:
        """test cusip"""
        expected_cusip = msft_cusip
        cusip = self.msft_ticker_from_ticker.cusip
        self.assertEqual(expected_cusip, cusip)

        cusip = self.msft_ticker_from_isin.cusip
        self.assertEqual(expected_cusip, cusip)

        cusip = self.msft_ticker_from_cusip.cusip
        self.assertEqual(expected_cusip, cusip)

        cusip = self.msft_ticker_from_id_triple.cusip
        self.assertEqual(expected_cusip, cusip)

    def test_history_metadata(self) -> None:
        """test history metadata"""
        expected_history_metadata = MOCK_TRADING_ITEM_DB[msft_trading_item_id]["metadata"].copy()
        expected_history_metadata["first_trade_date"] = datetime.strptime(
            expected_history_metadata["first_trade_date"], "%Y-%m-%d"
        ).date()
        history_metadata = self.msft_ticker_from_ticker.history_metadata
        expected_exchange_code = "NasdaqGS"
        self.assertEqual(expected_history_metadata, history_metadata)
        self.assertEqual(expected_exchange_code, self.msft_ticker_from_ticker.exchange_code)

        history_metadata = self.msft_ticker_from_isin.history_metadata
        self.assertEqual(expected_history_metadata, history_metadata)
        self.assertEqual(expected_exchange_code, self.msft_ticker_from_isin.exchange_code)

        history_metadata = self.msft_ticker_from_cusip.history_metadata
        self.assertEqual(expected_history_metadata, history_metadata)
        self.assertEqual(expected_exchange_code, self.msft_ticker_from_cusip.exchange_code)

        history_metadata = self.msft_ticker_from_id_triple.history_metadata
        self.assertEqual(expected_history_metadata, history_metadata)
        self.assertEqual(expected_exchange_code, self.msft_ticker_from_id_triple.exchange_code)

    def test_price_chart(self) -> None:
        """test price chart"""
        expected_price_chart = image_open(
            BytesIO(
                MOCK_TRADING_ITEM_DB[msft_trading_item_id]["price_chart"]["2020-01-01"][
                    "2021-01-01"
                ]
            )
        )
        price_chart = self.msft_ticker_from_ticker.price_chart(
            start_date="2020-01-01", end_date="2021-01-01"
        )
        self.assertEqual(expected_price_chart, price_chart)

        price_chart = self.msft_ticker_from_isin.price_chart(
            start_date="2020-01-01", end_date="2021-01-01"
        )
        self.assertEqual(expected_price_chart, price_chart)

        price_chart = self.msft_ticker_from_cusip.price_chart(
            start_date="2020-01-01", end_date="2021-01-01"
        )
        self.assertEqual(expected_price_chart, price_chart)

        price_chart = self.msft_ticker_from_id_triple.price_chart(
            start_date="2020-01-01", end_date="2021-01-01"
        )
        self.assertEqual(expected_price_chart, price_chart)

    def test_info(self) -> None:
        """test info"""
        expected_info = MOCK_COMPANY_DB[msft_company_id]["info"]
        info = self.msft_ticker_from_ticker.info
        self.assertEqual(expected_info, info)

        info = self.msft_ticker_from_isin.info
        self.assertEqual(expected_info, info)

        info = self.msft_ticker_from_cusip.info
        self.assertEqual(expected_info, info)

        info = self.msft_ticker_from_id_triple.info
        self.assertEqual(expected_info, info)

    def test_name(self) -> None:
        """test name"""
        expected_name = MOCK_COMPANY_DB[msft_company_id]["info"]["name"]
        name = self.msft_ticker_from_ticker.name
        self.assertEqual(expected_name, name)

        name = self.msft_ticker_from_isin.name
        self.assertEqual(expected_name, name)

        name = self.msft_ticker_from_cusip.name
        self.assertEqual(expected_name, name)

        name = self.msft_ticker_from_id_triple.name
        self.assertEqual(expected_name, name)

    def test_founding_date(self) -> None:
        """test founding date"""
        expected_founding_date = datetime.strptime(
            MOCK_COMPANY_DB[msft_company_id]["info"]["founding_date"], "%Y-%m-%d"
        ).date()
        founding_date = self.msft_ticker_from_ticker.founding_date
        self.assertEqual(expected_founding_date, founding_date)

        founding_date = self.msft_ticker_from_cusip.founding_date
        self.assertEqual(expected_founding_date, founding_date)

        founding_date = self.msft_ticker_from_isin.founding_date
        self.assertEqual(expected_founding_date, founding_date)

        founding_date = self.msft_ticker_from_id_triple.founding_date
        self.assertEqual(expected_founding_date, founding_date)

    def test_earnings_call_datetimes(self) -> None:
        """test earnings call datetimes"""
        expected_earnings_call_datetimes = [
            datetime.fromisoformat(
                MOCK_COMPANY_DB[msft_company_id]["earnings_call_dates"]["earnings"][0]
            ).replace(tzinfo=timezone.utc)
        ]
        earnings_call_datetimes = self.msft_ticker_from_ticker.earnings_call_datetimes
        self.assertEqual(expected_earnings_call_datetimes, earnings_call_datetimes)

        earnings_call_datetimes = self.msft_ticker_from_isin.earnings_call_datetimes
        self.assertEqual(expected_earnings_call_datetimes, earnings_call_datetimes)

        earnings_call_datetimes = self.msft_ticker_from_cusip.earnings_call_datetimes
        self.assertEqual(expected_earnings_call_datetimes, earnings_call_datetimes)

        earnings_call_datetimes = self.msft_ticker_from_id_triple.earnings_call_datetimes
        self.assertEqual(expected_earnings_call_datetimes, earnings_call_datetimes)

    def test_income_statement(self) -> None:
        """test income statement"""
        expected_income_statement = (
            pd.DataFrame(
                MOCK_COMPANY_DB[msft_company_id]["statements"]["income_statement"]["statements"]
            )
            .apply(pd.to_numeric)
            .replace(np.nan, None)
        )
        income_statement = self.msft_ticker_from_ticker.income_statement()
        pd.testing.assert_frame_equal(expected_income_statement, income_statement)

        income_statement = self.msft_ticker_from_isin.income_statement()
        pd.testing.assert_frame_equal(expected_income_statement, income_statement)

        income_statement = self.msft_ticker_from_cusip.income_statement()
        pd.testing.assert_frame_equal(expected_income_statement, income_statement)

        income_statement = self.msft_ticker_from_id_triple.income_statement()
        pd.testing.assert_frame_equal(expected_income_statement, income_statement)

    def test_revenue(self) -> None:
        """test revenue"""
        expected_revenue = (
            pd.DataFrame(MOCK_COMPANY_DB[msft_company_id]["line_items"]["revenue"])
            .transpose()
            .apply(pd.to_numeric)
            .replace(np.nan, None)
            .set_index(pd.Index(["revenue"]))
        )
        revenue = self.msft_ticker_from_ticker.revenue()
        pd.testing.assert_frame_equal(expected_revenue, revenue)

        revenue = self.msft_ticker_from_isin.revenue()
        pd.testing.assert_frame_equal(expected_revenue, revenue)

        revenue = self.msft_ticker_from_cusip.revenue()
        pd.testing.assert_frame_equal(expected_revenue, revenue)

        revenue = self.msft_ticker_from_id_triple.revenue()
        pd.testing.assert_frame_equal(expected_revenue, revenue)

    def test_ticker_symbol(self):
        """test ticker symbol"""
        expected_ticker_symbol = "MSFT"
        self.assertEqual(expected_ticker_symbol, self.msft_ticker_from_ticker.ticker)
        self.assertEqual(expected_ticker_symbol, self.msft_ticker_from_isin.ticker)
        self.assertEqual(expected_ticker_symbol, self.msft_ticker_from_cusip.ticker)
        self.assertEqual(expected_ticker_symbol, self.msft_ticker_from_id_triple.ticker)

    def test_market_cap(self):
        """
        GIVEN a mock client
        WHEN the mock client receives a mock market cap response dict
        THEN the Ticker object can correctly extract market caps from the dict.
        """

        expected_dataframe = pd.DataFrame(
            {"market_cap": {"2025-01-01": 3133802247084.0, "2025-01-02": 3112092395218.0}}
        )
        expected_dataframe.index.name = "date"
        market_caps = self.msft_ticker_from_ticker.market_cap()
        pd.testing.assert_frame_equal(expected_dataframe, market_caps)
