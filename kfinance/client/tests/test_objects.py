import copy
from datetime import date, datetime, timezone
from io import BytesIO
import re
from typing import Optional
from unittest import TestCase

import numpy as np
import pandas as pd
from PIL.Image import open as image_open
import time_machine

from kfinance.client.kfinance import (
    BusinessRelationships,
    Company,
    Earnings,
    MergerOrAcquisition,
    ParticipantInMerger,
    Security,
    Ticker,
    TradingItem,
    Transcript,
)
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
    RelationshipResponse,
)
from kfinance.domains.capitalizations.capitalization_models import Capitalizations
from kfinance.domains.companies.company_models import CompanyIdAndName
from kfinance.domains.earnings.earning_models import EarningsCallResp
from kfinance.domains.line_items.line_item_models import LineItemResponse


msft_company_id = "21835"
msft_security_id = "2630412"
msft_isin = "US5949181045"
msft_cusip = "594918104"
msft_trading_item_id = "2630413"
msft_buys_mongo = "517414"


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
        "earnings": EarningsCallResp.model_validate(
            {
                "earnings": [
                    {
                        "name": "Microsoft Corporation, Q4 2024 Earnings Call, Jul 25, 2024",
                        "key_dev_id": 1916266380,
                        "datetime": "2024-07-25T21:30:00Z",
                    },
                    {
                        "name": "Microsoft Corporation, Q1 2025 Earnings Call, Oct 24, 2024",
                        "key_dev_id": 1916266381,
                        "datetime": "2024-10-24T21:30:00Z",
                    },
                    {
                        "name": "Microsoft Corporation, Q2 2025 Earnings Call, Jan 25, 2025",
                        "key_dev_id": 1916266382,
                        "datetime": "2025-01-25T21:30:00Z",
                    },
                ]
            }
        ),
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
            "revenue": LineItemResponse.model_validate(
                {
                    "line_item": {
                        "2019": "125843000000.000000",
                        "2020": "143015000000.000000",
                        "2021": "168088000000.000000",
                        "2022": "198270000000.000000",
                        "2023": "211915000000.000000",
                    }
                }
            )
        },
        "segments": {
            "2024": {
                "Intelligent Cloud": {"Operating Income": 49584000000.0, "Revenue": 105362000000.0},
                "More Personal Computing": {
                    "Operating Income": 19309000000.0,
                    "Revenue": 62032000000.0,
                },
                "Productivity and Business Processes": {
                    "Operating Income": 40540000000.0,
                    "Revenue": 77728000000.0,
                },
            }
        },
        "mergers": {
            "target": [
                {
                    "transaction_id": 10998717,
                    "merger_title": "Closed M/A of Microsoft Corporation",
                    "closed_date": "2021-01-01",
                },
                {
                    "transaction_id": 28237969,
                    "merger_title": "Closed M/A of Microsoft Corporation",
                    "closed_date": "2022-01-01",
                },
            ],
            "buyer": [
                {
                    "transaction_id": 517414,
                    "merger_title": "Closed M/A of MongoMusic, Inc.",
                    "closed_date": "2023-01-01",
                },
                {
                    "transaction_id": 596722,
                    "merger_title": "Closed M/A of Digital Anvil, Inc.",
                    "closed_date": "2023-01-01",
                },
            ],
            "seller": [
                {
                    "transaction_id": 455551,
                    "merger_title": "Closed M/A of VacationSpot.com, Inc.",
                    "closed_date": "2024-01-01",
                },
                {
                    "transaction_id": 456045,
                    "merger_title": "Closed M/A of TransPoint, LLC",
                    "closed_date": "2025-01-01",
                },
            ],
        },
        "advisors": {
            msft_buys_mongo: {
                "advisors": [
                    {
                        "advisor_company_id": 251994106,
                        "advisor_company_name": "Kensho Technologies, Inc.",
                        "advisor_type_name": "Professional Mongo Enjoyer",
                    }
                ]
            }
        },
        BusinessRelationshipType.supplier: RelationshipResponse(
            current=[CompanyIdAndName(company_name="foo", company_id=883103)],
            previous=[
                CompanyIdAndName(company_name="bar", company_id=472898),
                CompanyIdAndName(company_name="baz", company_id=8182358),
            ],
        ),
    },
    31696: {"info": {"name": "MongoMusic, Inc."}},
    21835: {"info": {"name": "Microsoft Corporation"}},
    18805: {"info": {"name": "Angel Investors L.P."}},
    20087: {"info": {"name": "Draper Richards, L.P."}},
    22103: {"info": {"name": "BRV Partners, LLC"}},
    23745: {"info": {"name": "Venture Frogs, LLC"}},
    105902: {"info": {"name": "ARGUS Capital International Limited"}},
    880300: {"info": {"name": "Sony Music Entertainment, Inc."}},
}

MOCK_TRANSCRIPT_DB = {
    1916266380: {
        "transcript": [
            {
                "component_type": "Presentation Operator Message",
                "person_name": "Operator",
                "text": "Good morning, and welcome to Microsoft's Fourth Quarter 2024 Earnings Conference Call.",
            },
            {
                "component_type": "Presenter Speech",
                "person_name": "Satya Nadella",
                "text": "Thank you for joining us today. We had an exceptional quarter with strong growth across all segments.",
            },
        ]
    },
    1916266381: {
        "transcript": [
            {
                "component_type": "Presentation Operator Message",
                "person_name": "Operator",
                "text": "Good morning, and welcome to Microsoft's First Quarter 2025 Earnings Conference Call.",
            }
        ]
    },
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

MOCK_MERGERS_DB = {
    msft_buys_mongo: {
        "timeline": [
            {"status": "Announced", "date": "2000-09-12"},
            {"status": "Closed", "date": "2000-09-12"},
        ],
        "participants": {
            "target": {"company_id": 31696, "company_name": "MongoMusic, Inc."},
            "buyers": [{"company_id": 21835, "company_name": "Microsoft Corporation"}],
            "sellers": [
                {"company_id": 18805, "company_name": "Angel Investors L.P."},
                {"company_id": 20087, "company_name": "Draper Richards, L.P."},
                {"company_id": 22103, "company_name": "BRV Partners, LLC"},
                {"company_id": 23745, "company_name": "Venture Frogs, LLC"},
                {"company_id": 105902, "company_name": "ARGUS Capital International Limited"},
                {"company_id": 880300, "company_name": "Sony Music Entertainment, Inc."},
            ],
        },
        "consideration": {
            "currency_name": "US Dollar",
            "current_calculated_gross_total_transaction_value": "51609375.000000",
            "current_calculated_implied_equity_value": "51609375.000000",
            "current_calculated_implied_enterprise_value": "51609375.000000",
            "details": [
                {
                    "scenario": "Stock Lump Sum",
                    "subtype": "Common Equity",
                    "cash_or_cash_equivalent_per_target_share_unit": None,
                    "number_of_target_shares_sought": "1000000.000000",
                    "current_calculated_gross_value_of_consideration": "51609375.000000",
                }
            ],
        },
    }
}


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


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
    ) -> Capitalizations:
        return Capitalizations.model_validate(
            {
                "currency": "USD",
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
                ],
            }
        )

    def fetch_segments(
        self,
        company_id,
        segment_type,
        period_type,
        start_year,
        end_year,
        start_quarter,
        end_quarter,
    ):
        """Get a segment"""
        return MOCK_COMPANY_DB[company_id]

    def fetch_companies_from_business_relationship(
        self, company_id: int, relationship_type: BusinessRelationshipType
    ) -> RelationshipResponse:
        return MOCK_COMPANY_DB[company_id][relationship_type]

    def fetch_earnings(self, company_id: int) -> dict:
        """Get the earnings for a company."""
        return MOCK_COMPANY_DB[company_id]["earnings"]

    def fetch_transcript(self, key_dev_id: int) -> dict:
        """Get the transcript for an earnings item."""
        return MOCK_TRANSCRIPT_DB[key_dev_id]

    def fetch_mergers_for_company(self, company_id):
        return copy.deepcopy(MOCK_COMPANY_DB[company_id]["mergers"])

    def fetch_merger_info(self, transaction_id: int):
        return copy.deepcopy(MOCK_MERGERS_DB[str(transaction_id)])

    def fetch_advisors_for_company_in_merger(self, transaction_id, advised_company_id):
        return copy.deepcopy(MOCK_COMPANY_DB[advised_company_id]["advisors"][transaction_id])


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
        self.msft_company = ParticipantInMerger(
            kfinance_api_client=self.kfinance_api_client,
            transaction_id=msft_buys_mongo,
            company=Company(
                kfinance_api_client=self.kfinance_api_client,
                company_id=msft_company_id,
            ),
        )

    def test_company_id(self) -> None:
        """test company id"""
        expected_company_id = msft_company_id
        company_id = self.msft_company.company.company_id
        self.assertEqual(expected_company_id, company_id)

    def test_info(self) -> None:
        """test info"""
        expected_info = MOCK_COMPANY_DB[msft_company_id]["info"]
        info = self.msft_company.company.info
        self.assertEqual(expected_info, info)

    def test_name(self) -> None:
        """test name"""
        expected_name = MOCK_COMPANY_DB[msft_company_id]["info"]["name"]
        name = self.msft_company.company.name
        self.assertEqual(expected_name, name)

    def test_founding_date(self) -> None:
        """test founding date"""
        expected_founding_date = datetime.strptime(
            MOCK_COMPANY_DB[msft_company_id]["info"]["founding_date"], "%Y-%m-%d"
        ).date()
        founding_date = self.msft_company.company.founding_date
        self.assertEqual(expected_founding_date, founding_date)

    def test_earnings_call_datetimes(self) -> None:
        """test earnings call datetimes"""
        expected_earnings_call_datetimes = [
            datetime.fromisoformat(
                MOCK_COMPANY_DB[msft_company_id]["earnings_call_dates"]["earnings"][0]
            ).replace(tzinfo=timezone.utc)
        ]
        earnings_call_datetimes = self.msft_company.company.earnings_call_datetimes
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
        income_statement = self.msft_company.company.income_statement()
        pd.testing.assert_frame_equal(expected_income_statement, income_statement)

    def test_revenue(self) -> None:
        """test revenue"""
        line_item_response: LineItemResponse = MOCK_COMPANY_DB[msft_company_id]["line_items"][
            "revenue"
        ]
        expected_revenue = (
            pd.DataFrame({"line_item": line_item_response.line_item})
            .transpose()
            .apply(pd.to_numeric)
            .replace(np.nan, None)
            .set_index(pd.Index(["revenue"]))
        )
        revenue = self.msft_company.company.revenue()
        pd.testing.assert_frame_equal(expected_revenue, revenue)

    def test_business_segments(self) -> None:
        """test business statement"""
        expected_segments = MOCK_COMPANY_DB[msft_company_id]["segments"]

        business_segment = self.msft_company.company.business_segments()
        self.assertEqual(expected_segments, business_segment)

    def test_relationships(self) -> None:
        """
        WHEN we fetch the relationships of a company
        THEN we get back a BusinessRelationships object.
        """

        expected_suppliers = MOCK_COMPANY_DB[msft_company_id][BusinessRelationshipType.supplier]

        suppliers_via_method = self.msft_company.company.relationships(
            BusinessRelationshipType.supplier
        )
        self.assertIsInstance(suppliers_via_method, BusinessRelationships)
        # Company ids should match
        self.assertEqual(
            sorted([c.company_id for c in suppliers_via_method.current]),
            sorted([c.company_id for c in expected_suppliers.current]),
        )
        self.assertEqual(
            sorted([c.company_id for c in suppliers_via_method.previous]),
            sorted([c.company_id for c in expected_suppliers.previous]),
        )

        # Fetching via property should return the same result
        suppliers_via_property = self.msft_company.company.supplier
        self.assertEqual(suppliers_via_property, suppliers_via_method)

    def test_mergers(self) -> None:
        expected_mergers = MOCK_COMPANY_DB[msft_company_id]["mergers"]
        mergers = self.msft_company.company.mergers_and_acquisitions
        mergers_json = {
            "target": [
                {
                    "transaction_id": merger.transaction_id,
                    "merger_title": merger.merger_title,
                    "closed_date": merger.closed_date,
                }
                for merger in mergers["target"]
            ],
            "buyer": [
                {
                    "transaction_id": merger.transaction_id,
                    "merger_title": merger.merger_title,
                    "closed_date": merger.closed_date,
                }
                for merger in mergers["buyer"]
            ],
            "seller": [
                {
                    "transaction_id": merger.transaction_id,
                    "merger_title": merger.merger_title,
                    "closed_date": merger.closed_date,
                }
                for merger in mergers["seller"]
            ],
        }
        self.assertEqual(ordered(expected_mergers), ordered(mergers_json))

    def test_advisors(self) -> None:
        expected_advisors_json = MOCK_COMPANY_DB[msft_company_id]["advisors"][msft_buys_mongo][
            "advisors"
        ]
        expected_company_ids: list[int] = []
        expected_advisor_type_names: list[str] = []
        for advisor in expected_advisors_json:
            expected_company_ids.append(int(advisor["advisor_company_id"]))
            expected_advisor_type_names.append(str(advisor["advisor_type_name"]))
        advisors = self.msft_company.advisors
        company_ids: list[int] = []
        advisor_type_names: list[str] = []
        for advisor in advisors:
            company_ids.append(advisor.company.company_id)
            advisor_type_names.append(advisor.advisor_type_name)
        self.assertListEqual(expected_company_ids, company_ids)
        self.assertListEqual(expected_advisor_type_names, advisor_type_names)


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
        line_item_response: LineItemResponse = MOCK_COMPANY_DB[msft_company_id]["line_items"][
            "revenue"
        ]
        expected_revenue = (
            pd.DataFrame({"line_item": line_item_response.line_item})
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

        expected_response = [
            {"date": "2025-01-01", "market_cap": {"unit": "USD", "value": "3133802247084.00"}},
            {"date": "2025-01-02", "market_cap": {"unit": "USD", "value": "3112092395218.00"}},
        ]
        market_caps = self.msft_ticker_from_ticker.market_cap()
        assert market_caps == expected_response


class TestTranscript(TestCase):
    def setUp(self):
        """setup tests"""
        self.transcript_components = [
            {
                "component_type": "Presentation Operator Message",
                "person_name": "Operator",
                "text": "Good morning, and welcome to Microsoft's Fourth Quarter 2024 Earnings Conference Call.",
            },
            {
                "component_type": "Presenter Speech",
                "person_name": "Satya Nadella",
                "text": "Thank you for joining us today. We had an exceptional quarter with strong growth across all segments.",
            },
        ]
        self.transcript = Transcript(self.transcript_components)

    def test_transcript_length(self):
        """test transcript length"""
        self.assertEqual(len(self.transcript), 2)

    def test_transcript_indexing(self):
        """test transcript indexing"""
        self.assertEqual(
            self.transcript[0].person_name, self.transcript_components[0]["person_name"]
        )
        self.assertEqual(self.transcript[0].text, self.transcript_components[0]["text"])
        self.assertEqual(
            self.transcript[0].component_type, self.transcript_components[0]["component_type"]
        )
        self.assertEqual(
            self.transcript[1].person_name, self.transcript_components[1]["person_name"]
        )
        self.assertEqual(self.transcript[1].text, self.transcript_components[1]["text"])
        self.assertEqual(
            self.transcript[1].component_type, self.transcript_components[1]["component_type"]
        )

    def test_transcript_raw(self):
        """test transcript raw property"""
        expected_raw = "Operator: Good morning, and welcome to Microsoft's Fourth Quarter 2024 Earnings Conference Call.\n\nSatya Nadella: Thank you for joining us today. We had an exceptional quarter with strong growth across all segments."
        self.assertEqual(self.transcript.raw, expected_raw)


class TestEarnings(TestCase):
    def setUp(self):
        """setup tests"""
        self.kfinance_api_client = MockKFinanceApiClient()
        self.earnings = Earnings(
            kfinance_api_client=self.kfinance_api_client,
            name="Microsoft Corporation, Q4 2024 Earnings Call, Jul 25, 2024",
            datetime=datetime.fromisoformat("2024-07-25T21:30:00").replace(tzinfo=timezone.utc),
            key_dev_id=1916266380,
        )

    def test_earnings_attributes(self):
        """test earnings attributes"""
        self.assertEqual(
            self.earnings.name, "Microsoft Corporation, Q4 2024 Earnings Call, Jul 25, 2024"
        )
        self.assertEqual(self.earnings.key_dev_id, 1916266380)
        expected_datetime = datetime.fromisoformat("2024-07-25T21:30:00").replace(
            tzinfo=timezone.utc
        )
        self.assertEqual(self.earnings.datetime, expected_datetime)

    def test_earnings_transcript(self):
        """test earnings transcript property"""
        transcript = self.earnings.transcript
        self.assertIsInstance(transcript, Transcript)
        self.assertEqual(len(transcript), 2)
        self.assertEqual(transcript[0].person_name, "Operator")
        self.assertEqual(transcript[1].person_name, "Satya Nadella")


class TestCompanyEarnings(TestCase):
    def setUp(self):
        """setup tests"""
        self.kfinance_api_client = MockKFinanceApiClient()
        self.msft_company = Company(self.kfinance_api_client, msft_company_id)

    def test_company_earnings(self):
        """test company earnings method"""
        earnings_list = self.msft_company.earnings()
        self.assertEqual(len(earnings_list), 3)
        self.assertIsInstance(earnings_list[0], Earnings)
        self.assertEqual(earnings_list[0].key_dev_id, 1916266380)

    def test_company_earnings_with_date_filter(self):
        """test company earnings method with date filtering"""
        start_date = date(2024, 8, 1)
        end_date = date(2024, 12, 31)
        earnings_list = self.msft_company.earnings(start_date=start_date, end_date=end_date)
        self.assertEqual(len(earnings_list), 1)
        self.assertEqual(earnings_list[0].key_dev_id, 1916266381)

    @time_machine.travel(datetime(2025, 2, 1, 12, tzinfo=timezone.utc))
    def test_company_latest_earnings(self):
        """test company latest_earnings property"""
        latest_earnings = self.msft_company.latest_earnings
        self.assertEqual(latest_earnings.key_dev_id, 1916266382)

    @time_machine.travel(datetime(2024, 6, 1, 12, tzinfo=timezone.utc))
    def test_company_next_earnings(self):
        """test company next_earnings property"""
        next_earnings = self.msft_company.next_earnings
        self.assertEqual(next_earnings.key_dev_id, 1916266380)


class TestMerger(TestCase):
    def setUp(self):
        self.kfinance_api_client = MockKFinanceApiClient()
        self.merger = MergerOrAcquisition(
            kfinance_api_client=self.kfinance_api_client,
            transaction_id=int(msft_buys_mongo),
            merger_title="Closed M/A of MongoMusic, Inc.",
            closed_date=date(2021, 1, 1),
        )

    def test_merger_info(self) -> None:
        expected_merger_info = MOCK_MERGERS_DB[msft_buys_mongo]
        merger_info = {
            "timeline": [
                {"status": timeline["status"], "date": timeline["date"].strftime("%Y-%m-%d")}
                for timeline in self.merger.get_timeline.to_dict(orient="records")
            ],
            "participants": {
                "target": {
                    "company_id": self.merger.get_participants["target"].company.company_id,
                    "company_name": self.merger.get_participants["target"].company.name,
                },
                "buyers": [
                    {"company_id": buyer.company.company_id, "company_name": buyer.company.name}
                    for buyer in self.merger.get_participants["buyers"]
                ],
                "sellers": [
                    {"company_id": seller.company.company_id, "company_name": seller.company.name}
                    for seller in self.merger.get_participants["sellers"]
                ],
            },
            "consideration": {
                "currency_name": self.merger.get_consideration["currency_name"],
                "current_calculated_gross_total_transaction_value": self.merger.get_consideration[
                    "current_calculated_gross_total_transaction_value"
                ],
                "current_calculated_implied_equity_value": self.merger.get_consideration[
                    "current_calculated_implied_equity_value"
                ],
                "current_calculated_implied_enterprise_value": self.merger.get_consideration[
                    "current_calculated_implied_enterprise_value"
                ],
                "details": [
                    {
                        "scenario": detail["scenario"],
                        "subtype": detail["subtype"],
                        "cash_or_cash_equivalent_per_target_share_unit": detail[
                            "cash_or_cash_equivalent_per_target_share_unit"
                        ],
                        "number_of_target_shares_sought": detail["number_of_target_shares_sought"],
                        "current_calculated_gross_value_of_consideration": detail[
                            "current_calculated_gross_value_of_consideration"
                        ],
                    }
                    for detail in self.merger.get_consideration["details"].to_dict(orient="records")
                ],
            },
        }
        self.assertEqual(ordered(expected_merger_info), ordered(merger_info))
