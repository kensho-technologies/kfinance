from datetime import date
from decimal import Decimal
from typing import Any

import httpx2
from pydantic import ValidationError
import pytest
from respx import Router

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.ownership.ownership_models import (
    CompanyOwners,
    CompanyRelationship,
    Holdings,
    HoldingsResp,
    InsiderTradesResp,
    OwnersResp,
    OwnersSummaryResp,
    OwnerTypeSummary,
)
from kfinance.domains.ownership.ownership_tools import (
    DEFAULT_INSIDER_TRADES_LIMIT,
    DEFAULT_OWNERS_AND_HOLDINGS_LIMIT,
    FIRST_APPEARANCE_NOTE,
    OWNERSHIP_PCT_OUT_OF_RANGE_NOTE,
    GetHoldingsFromIdentifiers,
    GetHoldingsFromIdentifiersArgs,
    GetHoldingsFromIdentifiersResp,
    GetInsiderTradesFromIdentifiers,
    GetInsiderTradesFromIdentifiersArgs,
    GetInsiderTradesFromIdentifiersResp,
    GetOwnersFromIdentifiers,
    GetOwnersFromIdentifiersArgs,
    GetOwnersFromIdentifiersResp,
    fetch_holdings_from_company_id,
    fetch_insider_trades_from_company_id,
    fetch_owners_from_company_id,
    fetch_owners_summary_from_company_id,
    get_holdings_from_identifiers,
    get_insider_trades_from_identifiers,
    get_owners_from_identifiers,
    owners_notes,
)


NON_EXISTENT_ID_ERROR = (
    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
)

OWNERS_URL = "https://kfinance.kensho.com/api/v1/ownership/owners/"
OWNERS_SUMMARY_URL = "https://kfinance.kensho.com/api/v1/ownership/owners_summary/"
HOLDINGS_URL = "https://kfinance.kensho.com/api/v1/ownership/holdings/"
INSIDER_TRADES_URL = "https://kfinance.kensho.com/api/v1/ownership/insider_trades/"


class TestOwnershipToolArgs:
    @pytest.mark.parametrize(
        "args_model",
        [
            GetOwnersFromIdentifiersArgs,
            GetHoldingsFromIdentifiersArgs,
            GetInsiderTradesFromIdentifiersArgs,
        ],
    )
    @pytest.mark.parametrize("limit", [0, -1])
    def test_limit_rejects_values_below_one(self, args_model: Any, limit: int) -> None:
        """
        WHEN a tool is called with a limit below 1
        THEN the args are rejected rather than silently dropping results
        """
        with pytest.raises(ValidationError):
            args_model(identifiers=["SPGI"], limit=limit)

    @pytest.mark.parametrize(
        "args_model, expected_limit",
        [
            pytest.param(
                GetOwnersFromIdentifiersArgs, DEFAULT_OWNERS_AND_HOLDINGS_LIMIT, id="owners"
            ),
            pytest.param(
                GetHoldingsFromIdentifiersArgs, DEFAULT_OWNERS_AND_HOLDINGS_LIMIT, id="holdings"
            ),
            # The insider trades limit depends on the date range, so it is applied when fetching.
            pytest.param(GetInsiderTradesFromIdentifiersArgs, None, id="insider trades"),
        ],
    )
    def test_limit_defaults(self, args_model: Any, expected_limit: int | None) -> None:
        """
        WHEN a tool is called without a limit
        THEN the owners and holdings tools default to the owners and holdings limit, and the
            insider trades tool leaves it unset
        """
        assert args_model(identifiers=["SPGI"]).limit == expected_limit

    @pytest.mark.parametrize(
        "args_model", [GetOwnersFromIdentifiersArgs, GetHoldingsFromIdentifiersArgs]
    )
    def test_limit_accepts_null(self, args_model: Any) -> None:
        """
        WHEN the owners or holdings tool is called with a null limit
        THEN no limit is applied
        """
        assert args_model(identifiers=["SPGI"], limit=None).limit is None

    @pytest.mark.parametrize("min_pct_shares_outstanding", [None, -1, 0, 5.5, 100, 100.5])
    def test_min_pct_shares_outstanding_is_unbounded(
        self, min_pct_shares_outstanding: float | None
    ) -> None:
        """
        WHEN the owners tool is called with a null min_pct_shares_outstanding or any number,
            including negatives and values over 100 (both occur in the source data)
        THEN the args are accepted
        """
        args = GetOwnersFromIdentifiersArgs(
            identifiers=["SPGI"], min_pct_shares_outstanding=min_pct_shares_outstanding
        )
        assert args.min_pct_shares_outstanding == min_pct_shares_outstanding

    def test_insider_trades_rejects_start_date_after_end_date(self) -> None:
        """
        WHEN the insider trades tool is called with a start_date after the end_date
        THEN the args are rejected
        """
        with pytest.raises(ValidationError, match="must be on or before end_date"):
            GetInsiderTradesFromIdentifiersArgs(
                identifiers=["SPGI"], start_date=date(2025, 1, 1), end_date=date(2024, 1, 1)
            )

    @pytest.mark.parametrize(
        "start_date, end_date",
        [
            pytest.param(date(2024, 1, 1), date(2024, 1, 1), id="same day"),
            pytest.param(date(2024, 1, 1), None, id="start only"),
            pytest.param(None, date(2024, 1, 1), id="end only"),
        ],
    )
    def test_insider_trades_accepts_valid_date_ranges(
        self, start_date: date | None, end_date: date | None
    ) -> None:
        """
        WHEN the insider trades tool is called with a single-day, open-ended, or ordered range
        THEN the args are accepted
        """
        args = GetInsiderTradesFromIdentifiersArgs(
            identifiers=["SPGI"], start_date=start_date, end_date=end_date
        )
        assert (args.start_date, args.end_date) == (start_date, end_date)


class TestGetOwners:
    spgi_owners_api_resp = {
        "results": {
            "ownership": [
                {
                    "owner_id": 265933,
                    "owner_name": "The Vanguard Group, Inc.",
                    "institution_type": "Investment Adviser",
                    "position": {
                        "shares_held": 30000000,
                        "percent_shares_outstanding": 9.8,
                        "shares_changed": 100000,
                        "percent_shares_changed": 0.33,
                        "holding_date": "2025-06-30T00:00:00",
                    },
                    "relationship": {
                        "relationship_type": "Current Investment",
                        "estimated_percent_ownership": 8.4,
                        "controlling_interest": False,
                    },
                },
                {
                    "owner_id": 12345,
                    "owner_name": "BlackRock, Inc.",
                    "institution_type": None,
                    "position": {
                        "shares_held": 25000000,
                        "percent_shares_outstanding": None,
                        "shares_changed": 25000000,
                        "percent_shares_changed": None,
                        "holding_date": "2025-06-30T00:00:00",
                    },
                    "relationship": None,
                },
                {
                    "owner_id": 32011,
                    "owner_name": "Strategic Investor Holdings LLC",
                    "institution_type": None,
                    "position": None,
                    "relationship": {
                        "relationship_type": "Current Investment",
                        "estimated_percent_ownership": 3.1,
                        "controlling_interest": False,
                    },
                },
            ]
        },
        "errors": {},
    }
    spgi_owners_summary_api_resp = {
        "results": {
            "institutional_shares_held": 270000000,
            "number_of_holders": 2500,
            "shares_bought": 10000000,
            "shares_sold": 8000000,
            "number_of_buyers": 900,
            "number_of_sellers": 800,
            "number_of_new_buyers": 100,
            "number_of_closed_positions": 50,
            "institutional_ownership_pct": 88.5,
            "by_owner_type": [
                {"owner_type": "Institutions", "shares_held": 270000000},
                {"owner_type": "Public and Other", "shares_held": 35000000},
            ],
        },
        "errors": {},
    }

    spgi_owners_resp = OwnersResp.model_validate(spgi_owners_api_resp)
    spgi_owners_summary_resp = OwnersSummaryResp.model_validate(spgi_owners_summary_api_resp)

    @pytest.mark.asyncio
    async def test_fetch_owners_from_company_id(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        WHEN we request SPGI's owners with a min_pct_shares_outstanding threshold
        THEN the threshold is sent to the server and we get back SPGI's owners
        """
        route = httpx2_mock.post(
            OWNERS_URL, json={"company_id": SPGI_COMPANY_ID, "min_pct_shares_outstanding": 5}
        ).respond(json=self.spgi_owners_api_resp)

        resp = await fetch_owners_from_company_id(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client, min_pct_shares_outstanding=5
        )

        assert route.called
        assert resp == self.spgi_owners_resp
        vanguard, blackrock, strategic_investor = resp.results.ownership
        assert vanguard.relationship == CompanyRelationship(
            relationship_type="Current Investment",
            estimated_percent_ownership=Decimal("8.4"),
            controlling_interest=False,
        )
        assert blackrock.position is not None
        assert blackrock.position.percent_shares_changed is None
        assert blackrock.relationship is None
        # Owners with only a Company Relationships relationship have no position.
        assert strategic_investor.position is None
        assert strategic_investor.relationship is not None

    @pytest.mark.asyncio
    async def test_fetch_owners_summary_from_company_id(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        WHEN we request SPGI's ownership summary
        THEN we get back SPGI's ownership summary
        """
        httpx2_mock.post(OWNERS_SUMMARY_URL, json={"company_id": SPGI_COMPANY_ID}).respond(
            json=self.spgi_owners_summary_api_resp
        )

        resp = await fetch_owners_summary_from_company_id(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client
        )

        assert resp == self.spgi_owners_summary_resp

    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN include_summary is False (the default)
        WHEN we fetch owners for SPGI and a non-existent company
        THEN we get back SPGI's owners without a summary and an error for the non-existent company,
            and the request leaves out the unset min_pct_shares_outstanding
        """
        # No owners_summary route is registered, so the test fails if the summary is fetched.
        # respx matches json exactly, so the test also fails if min_pct_shares_outstanding is sent.
        httpx2_mock.post(OWNERS_URL, json={"company_id": SPGI_COMPANY_ID}).respond(
            json=self.spgi_owners_api_resp
        )

        expected_resp = GetOwnersFromIdentifiersResp(
            identifier_results={
                "SPGI": CompanyOwners(owners=self.spgi_owners_resp.results.ownership)
            },
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            # BlackRock has no prior period
            notes=[FIRST_APPEARANCE_NOTE],
            errors=[NON_EXISTENT_ID_ERROR],
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI", "non-existent"], httpx_client=httpx_client
        )

        assert resp == expected_resp
        assert (
            "summary"
            not in resp.model_dump(mode="json", exclude_none=True)["results"]["SPGI"]["data"]
        )

    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers_with_summary_and_limit(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN include_summary is True and limit is 1
        WHEN we fetch owners for SPGI
        THEN we get back SPGI's ownership summary and only its largest owner, with notes only for
            the returned owners
        """
        httpx2_mock.post(OWNERS_URL).respond(json=self.spgi_owners_api_resp)
        httpx2_mock.post(OWNERS_SUMMARY_URL).respond(json=self.spgi_owners_summary_api_resp)

        expected_resp = GetOwnersFromIdentifiersResp(
            identifier_results={
                "SPGI": CompanyOwners(
                    summary=self.spgi_owners_summary_resp.results,
                    owners=self.spgi_owners_resp.results.ownership[:1],
                )
            },
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            # No FIRST_APPEARANCE_NOTE: BlackRock, the owner without a prior period, is cut by limit.
            notes=None,
            errors=[],
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, include_summary=True, limit=1
        )

        assert resp == expected_resp
        # With no notes, the field is left out of the tool output, like an empty errors list.
        assert "notes" not in resp.model_dump(mode="json", exclude_none=True)

    @pytest.mark.parametrize(
        "min_pct_shares_outstanding, expected_owner_ids",
        [
            pytest.param(3, [265933, 12345, 32011], id="all above threshold"),
            # BlackRock has no percent, so the client keeps it. (The server drops positions without a
            # percent when given a threshold, so it wouldn't return BlackRock in practice.)
            pytest.param(5, [265933, 12345], id="drops relationship below threshold"),
            # Vanguard's position percent (9.8) wins over its lower estimated percent (8.4).
            pytest.param(9, [265933, 12345], id="prefers position percent"),
            pytest.param(10, [12345], id="drops position below threshold"),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers_filters_by_min_pct(
        self,
        httpx_client: httpx2.AsyncClient,
        httpx2_mock: Router,
        min_pct_shares_outstanding: float,
        expected_owner_ids: list[int],
    ) -> None:
        """
        GIVEN the server returns owners it couldn't filter by min_pct_shares_outstanding
        WHEN we fetch owners for SPGI with a min_pct_shares_outstanding threshold
        THEN owners are filtered by their position's percent of shares outstanding, falling back
            to their relationship's estimated percent ownership, and the client keeps owners with
            neither
        """
        httpx2_mock.post(OWNERS_URL).respond(json=self.spgi_owners_api_resp)

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            min_pct_shares_outstanding=min_pct_shares_outstanding,
        )

        owners = resp.identifier_results["SPGI"].owners
        assert [owner.owner_id for owner in owners] == expected_owner_ids
        assert resp.errors == []

    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers_min_pct_filters_all_owners(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN the server only returns an owner with a relationship below the threshold
        WHEN we fetch owners for SPGI with a min_pct_shares_outstanding threshold
        THEN we get back no results and the same error the server gives when it filters all owners
        """
        strategic_investor = self.spgi_owners_api_resp["results"]["ownership"][2]
        httpx2_mock.post(OWNERS_URL).respond(
            json={"results": {"ownership": [strategic_investor]}, "errors": {}}
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, min_pct_shares_outstanding=5
        )

        assert resp.identifier_results == {}
        assert resp.errors == ["SPGI: No owners found."]

    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers_server_errors(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN the server finds no owners for SPGI but does have an ownership summary
        WHEN we fetch owners for SPGI with include_summary=True
        THEN we get back the summary and the server's owners error
        """
        httpx2_mock.post(OWNERS_URL).respond(
            json={
                "results": {"ownership": []},
                "errors": {str(SPGI_COMPANY_ID): "No owners found."},
            }
        )
        httpx2_mock.post(OWNERS_SUMMARY_URL).respond(json=self.spgi_owners_summary_api_resp)

        expected_resp = GetOwnersFromIdentifiersResp(
            identifier_results={
                "SPGI": CompanyOwners(summary=self.spgi_owners_summary_resp.results, owners=[])
            },
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=["SPGI: No owners found."],
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, include_summary=True
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers_dedupes_company_not_found(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN both the owners and owners_summary endpoints return "Company not found."
        WHEN we fetch owners for SPGI with include_summary=True
        THEN we get back no results and the error only once
        """
        error_resp = {"errors": {str(SPGI_COMPANY_ID): "Company not found."}}
        httpx2_mock.post(OWNERS_URL).respond(json={"results": {"ownership": []}, **error_resp})
        httpx2_mock.post(OWNERS_SUMMARY_URL).respond(json={"results": None, **error_resp})

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, include_summary=True
        )

        assert resp.identifier_results == {}
        assert resp.errors == ["SPGI: Company not found."]

    @pytest.mark.asyncio
    async def test_get_owners_from_identifiers_dedupes_request_errors(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN both the owners and owners_summary requests fail with the same 400 error
        WHEN we fetch owners for SPGI with include_summary=True
        THEN we get back no results and the error only once
        """
        httpx2_mock.post(OWNERS_URL).respond(status_code=400, text="Invalid request.")
        httpx2_mock.post(OWNERS_SUMMARY_URL).respond(status_code=400, text="Invalid request.")

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, include_summary=True
        )

        assert resp.identifier_results == {}
        assert resp.errors == ["Invalid request."]

    @pytest.mark.parametrize(
        "tool_args, expected_num_owners",
        [
            pytest.param({}, DEFAULT_OWNERS_AND_HOLDINGS_LIMIT, id="caps at the default"),
            pytest.param({"limit": 10}, 10, id="explicit limit overrides the default"),
            pytest.param({"limit": None}, 350, id="null limit removes the cap"),
        ],
    )
    @pytest.mark.asyncio
    async def test_owners_tool_default_limit(
        self,
        mock_client: Client,
        httpx2_mock: Router,
        tool_args: dict[str, Any],
        expected_num_owners: int,
    ) -> None:
        """
        GIVEN SPGI has 350 owners
        WHEN the owners tool runs with or without a limit
        THEN it caps the owners at the default limit unless a limit or a null limit is given
        """
        vanguard = self.spgi_owners_api_resp["results"]["ownership"][0]
        httpx2_mock.post(OWNERS_URL).respond(
            json={"results": {"ownership": [vanguard] * 350}, "errors": {}}
        )
        tool = GetOwnersFromIdentifiers(kfinance_client=mock_client)

        resp = await tool.arun_without_langchain(identifiers=["SPGI"], **tool_args)

        assert len(resp["results"]["SPGI"]["data"]["owners"]) == expected_num_owners


class TestGetHoldings:
    spgi_holdings_api_resp = {
        "results": {
            "holdings": [
                {
                    "held_company_id": 24937,
                    "held_company_name": "Apple Inc.",
                    "positions": [
                        {
                            "security_id": 2534,
                            "ticker": "NasdaqGS:AAPL",
                            "shares_held": 195000000,
                            "percent_of_portfolio": 5.2,
                            "percent_shares_outstanding": 8.5,
                            "holding_date": "2025-06-30T00:00:00",
                        }
                    ],
                    "relationship": {
                        "relationship_type": "Current Investment",
                        "estimated_percent_ownership": 8.4,
                        "controlling_interest": False,
                    },
                },
                {
                    "held_company_id": 32012,
                    "held_company_name": "Privately Held Co.",
                    "positions": [],
                    "relationship": {
                        "relationship_type": "Current Investment",
                        "estimated_percent_ownership": 40.0,
                        "controlling_interest": False,
                    },
                },
                {
                    "held_company_id": None,
                    "held_company_name": None,
                    "positions": [
                        {
                            "security_id": 9999,
                            "ticker": None,
                            "shares_held": 1000,
                            "percent_of_portfolio": None,
                            "percent_shares_outstanding": None,
                            "holding_date": "2025-06-30T00:00:00",
                        }
                    ],
                    "relationship": None,
                },
            ]
        },
        "errors": {},
    }

    spgi_holdings_resp = HoldingsResp.model_validate(spgi_holdings_api_resp)

    @pytest.mark.asyncio
    async def test_fetch_holdings_from_company_id(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        WHEN we request SPGI's holdings
        THEN we get back SPGI's holdings, including their relationships, with held company ids
            serialized with a C_ prefix
        """
        httpx2_mock.post(HOLDINGS_URL, json={"company_id": SPGI_COMPANY_ID}).respond(
            json=self.spgi_holdings_api_resp
        )

        resp = await fetch_holdings_from_company_id(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client
        )

        assert resp == self.spgi_holdings_resp
        apple, privately_held, unmapped = resp.results.holdings
        assert apple.positions and apple.relationship is not None
        # Holdings with only a Company Relationships relationship have no positions.
        assert privately_held.positions == []
        assert privately_held.relationship == CompanyRelationship(
            relationship_type="Current Investment",
            estimated_percent_ownership=Decimal("40.0"),
            controlling_interest=False,
        )
        assert unmapped.relationship is None
        serialized_holdings = resp.model_dump(mode="json")["results"]["holdings"]
        assert serialized_holdings[0]["held_company_id"] == "C_24937"
        assert serialized_holdings[1]["held_company_id"] == "C_32012"
        assert serialized_holdings[2]["held_company_id"] is None

    @pytest.mark.asyncio
    async def test_get_holdings_from_identifiers(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        WHEN we fetch the top holding for SPGI and a non-existent company
        THEN we get back SPGI's largest holding and an error for the non-existent company
        """
        httpx2_mock.post(HOLDINGS_URL).respond(json=self.spgi_holdings_api_resp)

        expected_resp = GetHoldingsFromIdentifiersResp(
            identifier_results={
                "SPGI": Holdings(holdings=self.spgi_holdings_resp.results.holdings[:1])
            },
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[NON_EXISTENT_ID_ERROR],
        )

        resp = await get_holdings_from_identifiers(
            identifiers=["SPGI", "non-existent"], httpx_client=httpx_client, limit=1
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_holdings_from_identifiers_server_error(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN the server finds no holdings for SPGI
        WHEN we fetch holdings for SPGI
        THEN we get back no results and the server's error
        """
        httpx2_mock.post(HOLDINGS_URL).respond(
            json={
                "results": {"holdings": []},
                "errors": {str(SPGI_COMPANY_ID): "No holdings found."},
            }
        )

        resp = await get_holdings_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        assert resp.identifier_results == {}
        assert resp.errors == ["SPGI: No holdings found."]

    @pytest.mark.parametrize(
        "tool_args, expected_num_holdings",
        [
            pytest.param({}, DEFAULT_OWNERS_AND_HOLDINGS_LIMIT, id="caps at the default"),
            pytest.param({"limit": 10}, 10, id="explicit limit overrides the default"),
            pytest.param({"limit": None}, 350, id="null limit removes the cap"),
        ],
    )
    @pytest.mark.asyncio
    async def test_holdings_tool_default_limit(
        self,
        mock_client: Client,
        httpx2_mock: Router,
        tool_args: dict[str, Any],
        expected_num_holdings: int,
    ) -> None:
        """
        GIVEN SPGI has 350 holdings
        WHEN the holdings tool runs with or without a limit
        THEN it caps the holdings at the default limit unless a limit or a null limit is given
        """
        apple = self.spgi_holdings_api_resp["results"]["holdings"][0]
        httpx2_mock.post(HOLDINGS_URL).respond(
            json={"results": {"holdings": [apple] * 350}, "errors": {}}
        )
        tool = GetHoldingsFromIdentifiers(kfinance_client=mock_client)

        resp = await tool.arun_without_langchain(identifiers=["SPGI"], **tool_args)

        assert len(resp["results"]["SPGI"]["data"]["holdings"]) == expected_num_holdings


class TestGetInsiderTrades:
    spgi_insider_trades_api_resp = {
        "results": {
            "trades": [
                {
                    "owner_id": 1,
                    "insider_name": "Jane Doe",
                    "transaction_type": "Sale",
                    "security_type": "Common Stock",
                    "shares": -5000.0,
                    "min_price": 500.0,
                    "max_price": 510.0,
                    "transaction_value_usd": 2525000.0,
                    "trade_date": "2025-06-15T00:00:00",
                    "filing_date": "2025-06-17T00:00:00",
                },
                {
                    "owner_id": 2,
                    "insider_name": "John Doe",
                    "transaction_type": "Open Market Acquisition",
                    "security_type": "Common Stock",
                    "shares": 1000.0,
                    "min_price": 400.0,
                    "max_price": 400.0,
                    "transaction_value_usd": 400000.0,
                    "trade_date": "2024-03-01T00:00:00",
                    "filing_date": "2024-03-04T00:00:00",
                },
                {
                    "owner_id": 3,
                    "insider_name": None,
                    "transaction_type": None,
                    "security_type": None,
                    "shares": None,
                    "min_price": None,
                    "max_price": None,
                    "transaction_value_usd": None,
                    "trade_date": None,
                    "filing_date": None,
                },
            ]
        },
        "errors": {},
    }

    spgi_insider_trades_resp = InsiderTradesResp.model_validate(spgi_insider_trades_api_resp)

    @pytest.mark.asyncio
    async def test_fetch_insider_trades_from_company_id(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        WHEN we request SPGI's insider trades
        THEN we get back SPGI's insider trades
        """
        httpx2_mock.post(INSIDER_TRADES_URL, json={"company_id": SPGI_COMPANY_ID}).respond(
            json=self.spgi_insider_trades_api_resp
        )

        resp = await fetch_insider_trades_from_company_id(
            company_id=SPGI_COMPANY_ID, httpx_client=httpx_client
        )

        assert resp == self.spgi_insider_trades_resp

    @pytest.mark.asyncio
    async def test_get_insider_trades_from_identifiers(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        WHEN we fetch insider trades for SPGI and a non-existent company
        THEN we get back all of SPGI's insider trades and an error for the non-existent company
        """
        httpx2_mock.post(INSIDER_TRADES_URL).respond(json=self.spgi_insider_trades_api_resp)

        expected_resp = GetInsiderTradesFromIdentifiersResp(
            identifier_results={"SPGI": self.spgi_insider_trades_resp.results},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[NON_EXISTENT_ID_ERROR],
        )

        resp = await get_insider_trades_from_identifiers(
            identifiers=["SPGI", "non-existent"], httpx_client=httpx_client
        )

        assert resp == expected_resp

    @pytest.mark.parametrize(
        "start_date, end_date, limit, expected_owner_ids",
        [
            pytest.param(date(2025, 1, 1), None, None, [1], id="start_date"),
            pytest.param(None, date(2024, 12, 31), None, [2], id="end_date"),
            pytest.param(date(2024, 3, 1), date(2025, 6, 15), None, [1, 2], id="inclusive range"),
            pytest.param(None, None, 2, [1, 2], id="limit keeps most recent"),
            pytest.param(date(2024, 1, 1), None, 1, [1], id="date filter then limit"),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_insider_trades_from_identifiers_filters(
        self,
        httpx_client: httpx2.AsyncClient,
        httpx2_mock: Router,
        start_date: date | None,
        end_date: date | None,
        limit: int | None,
        expected_owner_ids: list[int],
    ) -> None:
        """
        GIVEN a trade date range and/or a limit
        WHEN we fetch insider trades for SPGI
        THEN we only get back the most recent trades within the range, skipping trades without a trade date
        """
        httpx2_mock.post(INSIDER_TRADES_URL).respond(json=self.spgi_insider_trades_api_resp)

        resp = await get_insider_trades_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        trades = resp.identifier_results["SPGI"].trades
        assert [trade.owner_id for trade in trades] == expected_owner_ids

    @pytest.mark.asyncio
    async def test_get_insider_trades_from_identifiers_server_error(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """
        GIVEN the server finds no insider trades for SPGI
        WHEN we fetch insider trades for SPGI
        THEN we get back no results and the server's error
        """
        httpx2_mock.post(INSIDER_TRADES_URL).respond(
            json={
                "results": {"trades": []},
                "errors": {str(SPGI_COMPANY_ID): "No insider trades found."},
            }
        )

        expected_resp = GetInsiderTradesFromIdentifiersResp(
            identifier_results={},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=["SPGI: No insider trades found."],
        )

        resp = await get_insider_trades_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client
        )

        assert resp == expected_resp

    @pytest.mark.parametrize(
        "tool_args, expected_num_trades",
        [
            pytest.param({}, DEFAULT_INSIDER_TRADES_LIMIT, id="no dates caps at the default"),
            pytest.param({"limit": 150}, 150, id="explicit limit overrides the default"),
            pytest.param({"start_date": "2000-01-01"}, 250, id="start_date removes the cap"),
            pytest.param({"end_date": "2030-01-01"}, 250, id="end_date removes the cap"),
        ],
    )
    @pytest.mark.asyncio
    async def test_insider_trades_tool_default_limit(
        self,
        mock_client: Client,
        httpx2_mock: Router,
        tool_args: dict[str, Any],
        expected_num_trades: int,
    ) -> None:
        """
        GIVEN SPGI has 250 insider trades
        WHEN the insider trades tool runs with or without a date range or limit
        THEN it caps the trades at the default limit only when no date range or limit is given
        """
        trade = self.spgi_insider_trades_api_resp["results"]["trades"][0]
        httpx2_mock.post(INSIDER_TRADES_URL).respond(
            json={"results": {"trades": [trade] * 250}, "errors": {}}
        )
        tool = GetInsiderTradesFromIdentifiers(kfinance_client=mock_client)

        resp = await tool.arun_without_langchain(identifiers=["SPGI"], **tool_args)

        assert len(resp["results"]["SPGI"]["data"]["trades"]) == expected_num_trades


class TestOwnersNotes:
    vanguard, blackrock, strategic_investor = TestGetOwners.spgi_owners_resp.results.ownership
    spgi_summary = TestGetOwners.spgi_owners_summary_resp.results

    def test_owners_notes_for_an_owner_without_a_prior_period(self) -> None:
        """
        WHEN an owner without a prior period is returned
        THEN the first appearance note is added
        """
        notes = owners_notes([CompanyOwners(owners=[self.vanguard, self.blackrock])])
        assert notes == [FIRST_APPEARANCE_NOTE]

    def test_owners_notes_for_an_owner_without_a_position(self) -> None:
        """
        WHEN an owner with only a relationship and no position is returned
        THEN no notes are added
        """
        assert owners_notes([CompanyOwners(owners=[self.strategic_investor])]) == []

    def test_owners_notes_for_owners_with_prior_periods(self) -> None:
        """
        WHEN only owners with a prior period are returned
        THEN no notes are added
        """
        assert owners_notes([CompanyOwners(owners=[self.vanguard])]) == []

    def test_owners_notes_for_a_summary_within_range(self) -> None:
        """
        WHEN a summary with an in-range ownership percent and no negative owner type shares is
            returned
        THEN no notes are added
        """
        assert owners_notes([CompanyOwners(summary=self.spgi_summary)]) == []

    @pytest.mark.parametrize(
        "update",
        [
            pytest.param({"institutional_ownership_pct": Decimal("100.5")}, id="pct above 100"),
            pytest.param({"institutional_ownership_pct": Decimal("-1")}, id="pct below 0"),
            pytest.param(
                {
                    "by_owner_type": [
                        OwnerTypeSummary(owner_type="Public and Other", shares_held=-5)
                    ]
                },
                id="negative owner type shares",
            ),
        ],
    )
    def test_owners_notes_for_a_summary_out_of_range(self, update: dict[str, Any]) -> None:
        """
        WHEN a summary with an ownership percent outside 0-100 or negative owner type shares is
            returned
        THEN the out of range note is added
        """
        summary = self.spgi_summary.model_copy(update=update)
        assert owners_notes([CompanyOwners(summary=summary)]) == [OWNERSHIP_PCT_OUT_OF_RANGE_NOTE]

    def test_owners_notes_for_no_results(self) -> None:
        """
        WHEN no results are returned
        THEN no notes are added
        """
        assert owners_notes([]) == []
