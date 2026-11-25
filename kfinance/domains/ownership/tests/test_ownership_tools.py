from datetime import date
from typing import Any

import httpx2
from pydantic import ValidationError
import pytest
from respx import Router

from kfinance.client.kfinance import Client
from kfinance.conftest import (
    FAKE_COMPANY_1_ID_TRIPLE,
    NON_EXISTENT_ERROR,
    SPGI_COMPANY_ID,
    SPGI_ID_TRIPLE,
)
from kfinance.domains.corporate_tree.corporate_tree_models import CompanyType
from kfinance.domains.ownership.ownership_models import (
    HELD_COMPANY_TYPES_BY_CATEGORY,
    INSIDER_TRANSACTION_TYPE_ATTRIBUTES,
    OWNER_TYPES_BY_CATEGORY,
    ApiInsiderTransactionType,
    ApiOwnerType,
    FundsView,
    HeldCompanyTypeCategory,
    InsiderActivityType,
    InsiderTradesSortBy,
    OwnersSortBy,
    OwnerTypeCategory,
    OwnerTypeSummary,
    PositionChange,
    TransactionDirection,
    select_insider_transaction_types,
    sum_by_owner_type_category,
)
from kfinance.domains.ownership.ownership_tools import (
    FIRST_APPEARANCE_NOTE,
    OWNERSHIP_PCT_OUT_OF_RANGE_NOTE,
    GetHoldingsFromIdentifiersArgs,
    GetInsiderActivityFromIdentifiersArgs,
    GetOwnersFromIdentifiers,
    GetOwnersFromIdentifiersArgs,
    get_holdings_from_identifiers,
    get_insider_activity_from_identifiers,
    get_owners_from_identifiers,
)


BASE_URL = "https://kfinance.kensho.com/api/v1"
IDS_URL = f"{BASE_URL}/ids"
OWNERS_URL = f"{BASE_URL}/ownership/owners/"
OWNERS_SUMMARY_URL = f"{BASE_URL}/ownership/owners_summary/"
HOLDINGS_URL = f"{BASE_URL}/ownership/holdings/"
INSIDER_TRADES_URL = f"{BASE_URL}/ownership/insider_trades/"

OWNER_COMPANY_ID = FAKE_COMPANY_1_ID_TRIPLE.company_id
PERSON_ID = 555

# No limit is sent by default, so the API applies its own default.
DEFAULT_OWNERS_PAYLOAD = {
    "company_id": SPGI_COMPANY_ID,
    "funds_view": "exclude_funds",
    "sort_by": "shares_held",
}
DEFAULT_HOLDINGS_PAYLOAD = {"company_id": SPGI_COMPANY_ID}
DEFAULT_INSIDER_TRADES_PAYLOAD = {
    "company_id": SPGI_COMPANY_ID,
    "sort_by": "date",
    # The default activity_types, every transaction group, leave out disclosures.
    "transaction_types": [
        str(t)
        for t in INSIDER_TRANSACTION_TYPE_ATTRIBUTES
        if t
        not in (
            ApiInsiderTransactionType.intent_to_sell_form_144,
            ApiInsiderTransactionType.initial_statement_of_beneficial_ownership_form_3,
        )
    ],
}

HIGH_OWNERS_COVERAGE = {
    "total_owners": 2000,
    "total_pct_shares_outstanding": 85.0,
    "by_owner_type": [
        {"owner_type": "institution", "owners": 1900, "pct_shares_outstanding": 80.0}
    ],
    "funds": {"owners": 5000, "pct_shares_outstanding": 40.0},
}
HIGH_HOLDINGS_COVERAGE = {
    "total_held_companies": 50,
    "total_pct_portfolio": 100.0,
    "by_held_company_type": [
        {"company_type": "public_company", "held_companies": 50, "pct_portfolio": 100.0}
    ],
}


def make_owner(
    owner_id: int = 100,
    shares_held: int = 1000,
    shares_changed: int = 10,
    percent_shares_changed: float | None = 1.0,
) -> dict[str, Any]:
    return {
        "owner_id": owner_id,
        "owner_name": f"Owner {owner_id}",
        "owner_type": "institution",
        "institution_type": "Investment Adviser",
        "shares_held": shares_held,
        "percent_shares_outstanding": 8.5,
        "holding_date": "2026-06-30",
        "reporting_period": {"start_date": "2026-04-01", "end_date": "2026-06-30"},
        "period_change": {
            "shares_changed": shares_changed,
            "percent_shares_changed": percent_shares_changed,
        },
        "fund_parent": None,
    }


def owners_response(
    owners: list[dict[str, Any]] | None = None,
    total_matching: int | None = None,
    coverage: dict[str, Any] | None = HIGH_OWNERS_COVERAGE,
    errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    owners = [make_owner()] if owners is None else owners
    return {
        "results": {
            "owners": owners,
            "total_matching": len(owners) if total_matching is None else total_matching,
            "coverage": coverage,
        },
        "errors": errors or {},
    }


def make_holding(held_company_id: int = 24937) -> dict[str, Any]:
    return {
        "held_company_id": held_company_id,
        "held_company_name": "Apple Inc.",
        "held_company_type": "public_company",
        "total_percent_of_portfolio": 12.5,
        "positions": [
            {
                "security_id": 1,
                "ticker": "AAPL",
                "shares_held": 1000,
                "percent_of_portfolio": 12.5,
                "percent_shares_outstanding": 1.2,
                "holding_date": "2026-06-30",
            }
        ],
    }


def holdings_response(
    holdings: list[dict[str, Any]] | None = None,
    total_matching: int | None = None,
    coverage: dict[str, Any] | None = HIGH_HOLDINGS_COVERAGE,
    errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    holdings = [make_holding()] if holdings is None else holdings
    return {
        "results": {
            "holdings": holdings,
            "total_matching": len(holdings) if total_matching is None else total_matching,
            "coverage": coverage,
        },
        "errors": errors or {},
    }


def make_trade() -> dict[str, Any]:
    return {
        "owner_id": PERSON_ID,
        "insider_name": "Jane Doe",
        "transaction_type": "sale",
        "security_type": "Common Stock",
        "shares": -1000.0,
        "min_price": 500.0,
        "max_price": 510.0,
        "transaction_value_usd": -505000.0,
        "trade_date": "2026-05-01",
        "filing_date": "2026-05-03T00:00:00",
    }


def insider_trades_response(
    trades: list[dict[str, Any]] | None = None, total_matching: int | None = None
) -> dict[str, Any]:
    trades = [make_trade()] if trades is None else trades
    return {
        "results": {
            "trades": trades,
            "total_matching": len(trades) if total_matching is None else total_matching,
        },
        "errors": {},
    }


SUMMARY_RESPONSE = {
    "results": {
        "institutional_shares_held": 250000000,
        "number_of_holders": 2000,
        "shares_bought": 1000000,
        "shares_sold": 2000000,
        "number_of_buyers": 800,
        "number_of_sellers": 900,
        "number_of_new_buyers": 50,
        "number_of_closed_positions": 40,
        "institutional_ownership_pct": 85.0,
        "reporting_period": {"start_date": "2026-04-01", "end_date": "2026-06-30"},
        "by_owner_type": [
            {"owner_type": "institution", "shares_held": 250000000},
            {"owner_type": "public_and_other", "shares_held": 30000000},
            # An owner type the API doesn't know.
            {"owner_type": None, "shares_held": 1000},
        ],
    },
    "errors": {},
}


def mock_ids(httpx2_mock: Router, identifiers: list[str], data: dict[str, Any]) -> None:
    """Mock the /ids call for exactly these identifiers."""
    httpx2_mock.post(IDS_URL, json={"identifiers": identifiers}).respond(json={"data": data})


SPGI_AND_OWNER_IDS = {
    "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
    "C_1": FAKE_COMPANY_1_ID_TRIPLE.model_dump(mode="json"),
}


class TestCategoryMappings:
    def test_every_api_owner_type_is_in_exactly_one_category(self) -> None:
        mapped = [t for types in OWNER_TYPES_BY_CATEGORY.values() for t in types]
        assert sorted(mapped) == sorted(ApiOwnerType)
        assert OwnerTypeCategory.all not in OWNER_TYPES_BY_CATEGORY

    def test_every_company_type_is_in_exactly_one_held_company_category(self) -> None:
        mapped = [t for types in HELD_COMPANY_TYPES_BY_CATEGORY.values() for t in types]
        assert sorted(mapped) == sorted(CompanyType)
        assert HeldCompanyTypeCategory.all not in HELD_COMPANY_TYPES_BY_CATEGORY

    def test_every_transaction_type_has_attributes(self) -> None:
        assert sorted(INSIDER_TRANSACTION_TYPE_ATTRIBUTES) == sorted(ApiInsiderTransactionType)


T = ApiInsiderTransactionType
DISCLOSURES = {T.intent_to_sell_form_144, T.initial_statement_of_beneficial_ownership_form_3}
AUTOMATIC = {T.automatic_acquisition, T.automatic_disposition}


def selected(
    activity_types: list[str] | None = None, direction: str = "both"
) -> set[ApiInsiderTransactionType]:
    return set(
        select_insider_transaction_types(
            activity_types=(
                None if activity_types is None else [InsiderActivityType(t) for t in activity_types]
            ),
            direction=TransactionDirection(direction),
        )
    )


class TestSelectInsiderTransactionTypes:
    def test_groups_partition_the_transaction_types(self) -> None:
        """Every API type is in exactly one group, so a list of groups never double counts."""
        by_group = [selected([group]) for group in InsiderActivityType]
        assert sum(len(types) for types in by_group) == len(ApiInsiderTransactionType)
        assert set().union(*by_group) == set(ApiInsiderTransactionType)

    def test_default_is_every_transaction_but_no_disclosures(self) -> None:
        assert selected() == set(ApiInsiderTransactionType) - DISCLOSURES
        assert selected() == selected(["open_market", "automatic", "derivatives", "other"])

    def test_open_market(self) -> None:
        assert selected(["open_market"]) == {
            T.open_market_acquisition,
            T.open_market_disposition,
            T.open_market_derivative_acquisition,
            T.open_market_derivative_disposition,
        }

    def test_only_plan_sales(self) -> None:
        assert selected(["automatic"], "dispositions") == {T.automatic_disposition}

    def test_sales_outside_a_trading_plan(self) -> None:
        assert selected(["open_market", "derivatives", "other"], "dispositions") == {
            T.open_market_disposition,
            T.open_market_derivative_disposition,
            T.derivative_disposition_under_employee_benefit_plan,
            T.other_derivative_disposition,
            T.derivative_sale_to_issuer,
            T.derivative_exercise_and_sale,
            T.disposition_under_employee_benefit_plan,
            T.private_disposition,
            T.other_disposition,
            T.sale_to_issuer,
            T.sale,
        }

    def test_derivatives(self) -> None:
        assert selected(["derivatives"]) == {
            T.derivative_acquisition_under_employee_benefit_plan,
            T.derivative_disposition_under_employee_benefit_plan,
            T.other_derivative_acquisition,
            T.other_derivative_disposition,
            T.derivative_sale_to_issuer,
            T.derivative_exercise,
            T.derivative_exercise_and_retained_stock,
            T.derivative_exercise_and_sale,
        }

    def test_option_exercises_follow_their_net_direction(self) -> None:
        assert {T.derivative_exercise, T.derivative_exercise_and_retained_stock} <= selected(
            direction="acquisitions"
        )
        assert T.derivative_exercise_and_sale in selected(direction="dispositions")

    @pytest.mark.parametrize(
        "direction, expected",
        [
            ("both", DISCLOSURES),
            ("dispositions", {T.intent_to_sell_form_144}),
            ("acquisitions", set()),
        ],
    )
    def test_disclosures(self, direction: str, expected: set) -> None:
        assert selected(["disclosures"], direction) == expected

    def test_transactions_and_disclosures_together(self) -> None:
        assert selected(["automatic", "disclosures"], "dispositions") == {
            T.automatic_disposition,
            T.intent_to_sell_form_144,
        }

    def test_duplicate_groups_are_ignored(self) -> None:
        assert selected(["automatic", "automatic"]) == AUTOMATIC

    def test_only_disclosed_acquisitions_are_empty(self) -> None:
        """Of the single groups, only disclosures with acquisitions selects nothing."""
        empty = {
            (group, direction)
            for group in InsiderActivityType
            for direction in TransactionDirection
            if not selected([group], direction)
        }
        assert empty == {("disclosures", "acquisitions")}


class TestSumByOwnerTypeCategory:
    def test_sums_api_owner_types_into_categories(self) -> None:
        by_owner_type = [
            OwnerTypeSummary(owner_type="institution", shares_held=100),
            OwnerTypeSummary(owner_type="public_and_other", shares_held=500),
            OwnerTypeSummary(owner_type="strategic_vc_pe_firm", shares_held=50),
            OwnerTypeSummary(owner_type="individual_insider", shares_held=30),
            OwnerTypeSummary(owner_type="public_corporation", shares_held=20),
            OwnerTypeSummary(owner_type="private_corporation", shares_held=5),
            OwnerTypeSummary(owner_type="state_owned", shares_held=7),
            OwnerTypeSummary(owner_type="esop", shares_held=3),
            OwnerTypeSummary(owner_type="a_type_added_later", shares_held=2),
            OwnerTypeSummary(owner_type=None, shares_held=1),
        ]

        assert [
            (t.owner_type, t.shares_held) for t in sum_by_owner_type_category(by_owner_type)
        ] == [
            ("unattributed", 500),
            ("institutions", 150),
            ("individuals", 30),
            ("corporations", 25),
            ("other", 13),
        ]

    def test_empty(self) -> None:
        assert sum_by_owner_type_category([]) == []


class TestGetOwnersArgs:
    def test_owner_type_requires_exclude_funds(self) -> None:
        with pytest.raises(ValidationError, match="funds_view='exclude_funds'"):
            GetOwnersFromIdentifiersArgs(
                identifiers=["SPGI"], owner_type="institutions", funds_view="include_funds"
            )

    def test_position_changes_rejects_an_empty_list(self) -> None:
        with pytest.raises(ValidationError):
            GetOwnersFromIdentifiersArgs(identifiers=["SPGI"], position_changes=[])

    def test_owner_type_all_allows_any_funds_view(self) -> None:
        args = GetOwnersFromIdentifiersArgs(identifiers=["SPGI"], funds_view="funds_only")
        assert args.funds_view == FundsView.funds_only

    @pytest.mark.parametrize("limit", [0, -1])
    def test_limit_must_be_positive(self, limit: int) -> None:
        with pytest.raises(ValidationError):
            GetOwnersFromIdentifiersArgs(identifiers=["SPGI"], limit=limit)

    @pytest.mark.parametrize(
        "args_model",
        [
            GetOwnersFromIdentifiersArgs,
            GetHoldingsFromIdentifiersArgs,
            GetInsiderActivityFromIdentifiersArgs,
        ],
    )
    @pytest.mark.parametrize("limit", [None, "all", 25])
    def test_limit_accepts_null_all_and_positive_ints(self, args_model: Any, limit: Any) -> None:
        assert args_model(identifiers=["SPGI"], limit=limit).limit == limit

    def test_limit_is_unset_when_omitted(self) -> None:
        assert GetOwnersFromIdentifiersArgs(identifiers=["SPGI"]).limit is None

    @pytest.mark.parametrize("limit", ["ALL", "none", "unlimited", 1.5])
    def test_limit_rejects_other_values(self, limit: Any) -> None:
        """The API only accepts "all" in lowercase, so anything else fails before a request."""
        with pytest.raises(ValidationError):
            GetOwnersFromIdentifiersArgs(identifiers=["SPGI"], limit=limit)

    @pytest.mark.asyncio
    async def test_explicit_null_limit_through_the_tool_sends_no_limit(
        self, mock_client: Client, httpx2_mock: Router
    ) -> None:
        """WHEN a model sends limit=null THEN no limit is sent, so the API applies its default."""
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(json=owners_response())

        resp = await GetOwnersFromIdentifiers(kfinance_client=mock_client).arun_without_langchain(
            identifiers=["SPGI"], limit=None
        )

        assert "SPGI" in resp["results"]


class TestGetOwners:
    @pytest.mark.asyncio
    async def test_default_request(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN no filters are given THEN only the defaults are sent and the owners returned."""
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(json=owners_response())

        resp = await get_owners_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        result = resp.identifier_results["SPGI"]
        assert result.total_matching == 1
        assert result.owners[0].owner_id == 100
        assert result.summary is None
        assert resp.notes is None
        assert resp.errors == []

    @pytest.mark.asyncio
    async def test_filters_are_expanded_into_the_request(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN filters are given THEN categories are expanded and limit="all" is sent as is."""
        httpx2_mock.post(
            OWNERS_URL,
            json={
                "company_id": SPGI_COMPANY_ID,
                "funds_view": "exclude_funds",
                "sort_by": "absolute_shares_changed",
                "limit": "all",
                "owner_types": ["public_corporation", "private_corporation"],
                "position_changes": ["new", "closed"],
                "min_pct_shares_outstanding": 5.0,
            },
        ).respond(json=owners_response())

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            owner_type=OwnerTypeCategory.corporations,
            position_changes=[PositionChange.new, PositionChange.closed],
            min_pct_shares_outstanding=5.0,
            sort_by=OwnersSortBy.absolute_shares_changed,
            limit="all",
        )

        assert "SPGI" in resp.identifier_results

    @pytest.mark.asyncio
    async def test_owner_company_identifiers_and_person_ids_are_combined(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN owner companies and people are given THEN both are sent as owner_ids."""
        mock_ids(httpx2_mock, ["SPGI", "C_1"], SPGI_AND_OWNER_IDS)
        httpx2_mock.post(
            OWNERS_URL, json={**DEFAULT_OWNERS_PAYLOAD, "owner_ids": [OWNER_COMPANY_ID, PERSON_ID]}
        ).respond(json=owners_response())

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            owner_company_identifiers=["C_1"],
            owner_person_ids=[PERSON_ID],
        )

        # Filter identifiers are not results.
        assert list(resp.identifier_results) == ["SPGI"]

    @pytest.mark.asyncio
    async def test_partially_unresolved_owner_identifiers(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN some owner identifiers fail THEN the rest are used and the failure reported."""
        mock_ids(
            httpx2_mock,
            ["SPGI", "C_1", "non-existent-company"],
            {**SPGI_AND_OWNER_IDS, "non-existent-company": NON_EXISTENT_ERROR},
        )
        httpx2_mock.post(
            OWNERS_URL, json={**DEFAULT_OWNERS_PAYLOAD, "owner_ids": [OWNER_COMPANY_ID]}
        ).respond(json=owners_response())

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            owner_company_identifiers=["C_1", "non-existent-company"],
        )

        assert "SPGI" in resp.identifier_results
        assert len(resp.errors) == 1
        assert "non-existent-company" in resp.errors[0]

    @pytest.mark.asyncio
    async def test_unresolved_owner_identifiers_skip_the_data_call(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN no owner identifier resolves THEN owners aren't fetched unfiltered."""
        mock_ids(
            httpx2_mock,
            ["SPGI", "non-existent-company"],
            {
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
                "non-existent-company": NON_EXISTENT_ERROR,
            },
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            owner_company_identifiers=["non-existent-company"],
        )

        assert resp.identifier_results == {}
        assert len(resp.errors) == 2
        assert any("None of the owner_company_identifiers" in e for e in resp.errors)

    @pytest.mark.asyncio
    async def test_unresolved_owner_identifiers_with_person_ids_still_fetch(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN no owner company resolves but people are given THEN the people are fetched."""
        mock_ids(
            httpx2_mock,
            ["SPGI", "non-existent-company"],
            {
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
                "non-existent-company": NON_EXISTENT_ERROR,
            },
        )
        httpx2_mock.post(
            OWNERS_URL, json={**DEFAULT_OWNERS_PAYLOAD, "owner_ids": [PERSON_ID]}
        ).respond(json=owners_response())

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            owner_company_identifiers=["non-existent-company"],
            owner_person_ids=[PERSON_ID],
        )

        assert "SPGI" in resp.identifier_results

    @pytest.mark.asyncio
    async def test_truncation_and_first_appearance_notes(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN the limit cuts results and an owner is new THEN both notes are added."""
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(
            json=owners_response(
                owners=[make_owner(percent_shares_changed=None, shares_changed=1000)],
                total_matching=2500,
            )
        )

        resp = await get_owners_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        assert resp.notes is not None
        assert resp.notes[0] == (
            "SPGI: returned 1 of 2,500 matching owners. "
            "Set a higher limit, or 'all' for no limit, to see more."
        )
        assert FIRST_APPEARANCE_NOTE in resp.notes

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "coverage, detail",
        [
            pytest.param(
                {"total_owners": 3, "total_pct_shares_outstanding": 12.34},
                "the owners found hold 12.3% of shares outstanding",
                id="low_pct",
            ),
            pytest.param(
                {"total_owners": 3, "total_pct_shares_outstanding": None},
                "no owner has a known percent of shares outstanding",
                id="unknown_pct",
            ),
            pytest.param(
                {"total_owners": 0, "total_pct_shares_outstanding": None},
                "no owners found",
                id="no_owners",
            ),
        ],
    )
    async def test_low_coverage_note(
        self,
        httpx_client: httpx2.AsyncClient,
        httpx2_mock: Router,
        coverage: dict[str, Any],
        detail: str,
    ) -> None:
        """WHEN the dataset covers little of the company THEN the note points to the corporate tree."""
        owners = [] if coverage["total_owners"] == 0 else None
        errors = {str(SPGI_COMPANY_ID): "No owners found."} if owners == [] else None
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(
            json=owners_response(owners=owners, coverage=coverage, errors=errors)
        )

        resp = await get_owners_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        assert resp.notes is not None
        note = resp.notes[-1]
        assert note.startswith(f"SPGI: The ownership coverage in this dataset is low ({detail}).")
        assert "get_ultimate_parent_paths_from_identifiers" in note
        if owners == []:
            assert resp.identifier_results == {}
            assert "No owners found." in resp.errors[0]

    @pytest.mark.asyncio
    async def test_high_coverage_has_no_note(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(
            json=owners_response(
                coverage={"total_owners": 10, "total_pct_shares_outstanding": 50.0}
            )
        )

        resp = await get_owners_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        assert resp.notes is None

    @pytest.mark.asyncio
    async def test_include_summary(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN include_summary is set THEN the summary is merged into the identifier's result."""
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(json=owners_response())
        httpx2_mock.post(OWNERS_SUMMARY_URL, json={"company_id": SPGI_COMPANY_ID}).respond(
            json=SUMMARY_RESPONSE
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, include_summary=True
        )

        result = resp.identifier_results["SPGI"]
        assert result.summary is not None
        assert result.summary.number_of_holders == 2000
        # Summed into the tool's owner_type categories; the unknown type counts as other.
        assert [(t.owner_type, t.shares_held) for t in result.summary.by_owner_type] == [
            ("institutions", 250000000),
            ("unattributed", 30000000),
            ("other", 1000),
        ]
        assert len(result.owners) == 1

    @pytest.mark.asyncio
    async def test_summary_out_of_range_note_and_error_dedup(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """WHEN both calls report the same error THEN it is only reported once."""
        error = {str(SPGI_COMPANY_ID): "Company not found."}
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(
            json=owners_response(owners=[], coverage=None, errors=error)
        )
        summary = {
            "results": {**SUMMARY_RESPONSE["results"], "institutional_ownership_pct": 120.0},
            "errors": error,
        }
        httpx2_mock.post(OWNERS_SUMMARY_URL, json={"company_id": SPGI_COMPANY_ID}).respond(
            json=summary
        )

        resp = await get_owners_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, include_summary=True
        )

        assert len(resp.errors) == 1
        assert resp.notes == [OWNERSHIP_PCT_OUT_OF_RANGE_NOTE]

    @pytest.mark.asyncio
    async def test_serialized_output_omits_coverage(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(OWNERS_URL, json=DEFAULT_OWNERS_PAYLOAD).respond(json=owners_response())

        resp = await get_owners_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)
        output = resp.model_dump(mode="json", exclude_none=True)

        data = output["results"]["SPGI"]["data"]
        assert set(data) == {"owners", "total_matching"}
        assert "errors" not in output


class TestGetHoldings:
    @pytest.mark.asyncio
    async def test_default_request(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(HOLDINGS_URL, json=DEFAULT_HOLDINGS_PAYLOAD).respond(
            json=holdings_response()
        )

        resp = await get_holdings_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        result = resp.identifier_results["SPGI"]
        assert result.total_matching == 1
        assert resp.notes is None
        # Held company ids serialize with the company prefix so they can be passed as identifiers.
        output = resp.model_dump(mode="json", exclude_none=True)
        assert output["results"]["SPGI"]["data"]["holdings"][0]["held_company_id"] == "C_24937"

    @pytest.mark.asyncio
    async def test_filters_are_expanded_into_the_request(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        mock_ids(httpx2_mock, ["SPGI", "C_1"], SPGI_AND_OWNER_IDS)
        httpx2_mock.post(
            HOLDINGS_URL,
            json={
                "company_id": SPGI_COMPANY_ID,
                "limit": 10,
                "held_company_types": ["public_fund", "private_fund", "fund_family"],
                "held_company_ids": [OWNER_COMPANY_ID],
                "min_pct_portfolio": 1.0,
                "min_pct_shares_outstanding": 2.0,
            },
        ).respond(json=holdings_response())

        resp = await get_holdings_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            held_company_type=HeldCompanyTypeCategory.funds,
            held_company_identifiers=["C_1"],
            min_pct_portfolio=1.0,
            min_pct_shares_outstanding=2.0,
            limit=10,
        )

        assert "SPGI" in resp.identifier_results

    @pytest.mark.asyncio
    async def test_unresolved_held_company_identifiers_skip_the_data_call(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        mock_ids(
            httpx2_mock,
            ["SPGI", "non-existent-company"],
            {
                "SPGI": SPGI_ID_TRIPLE.model_dump(mode="json"),
                "non-existent-company": NON_EXISTENT_ERROR,
            },
        )

        resp = await get_holdings_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            held_company_identifiers=["non-existent-company"],
        )

        assert resp.identifier_results == {}
        assert any("None of the held_company_identifiers" in e for e in resp.errors)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "coverage, detail",
        [
            pytest.param(
                {"total_held_companies": 3, "total_pct_portfolio": 100.0},
                "only 3 held companies found",
                id="few_holdings",
            ),
            pytest.param(
                {"total_held_companies": 30, "total_pct_portfolio": None},
                "no holding has a known percent of portfolio",
                id="unknown_pct",
            ),
            pytest.param(
                {"total_held_companies": 0, "total_pct_portfolio": None},
                "no holdings found",
                id="no_holdings",
            ),
        ],
    )
    async def test_low_coverage_note(
        self,
        httpx_client: httpx2.AsyncClient,
        httpx2_mock: Router,
        coverage: dict[str, Any],
        detail: str,
    ) -> None:
        holdings = [] if coverage["total_held_companies"] == 0 else None
        httpx2_mock.post(HOLDINGS_URL, json=DEFAULT_HOLDINGS_PAYLOAD).respond(
            json=holdings_response(holdings=holdings, coverage=coverage)
        )

        resp = await get_holdings_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        assert resp.notes is not None
        assert resp.notes[-1].startswith(
            f"SPGI: The ownership coverage in this dataset is low ({detail})."
        )
        assert "search_corporate_tree_from_identifiers" in resp.notes[-1]

    @pytest.mark.asyncio
    async def test_truncation_note(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(HOLDINGS_URL, json=DEFAULT_HOLDINGS_PAYLOAD).respond(
            json=holdings_response(total_matching=14257)
        )

        resp = await get_holdings_from_identifiers(identifiers=["SPGI"], httpx_client=httpx_client)

        assert resp.notes == [
            "SPGI: returned 1 of 14,257 matching held companies. "
            "Set a higher limit, or 'all' for no limit, to see more."
        ]


class TestGetInsiderActivityArgs:
    def test_start_date_must_not_be_after_end_date(self) -> None:
        with pytest.raises(ValidationError, match="must be on or before"):
            GetInsiderActivityFromIdentifiersArgs(
                identifiers=["SPGI"], start_date="2025-01-02", end_date="2025-01-01"
            )

    def test_defaults(self) -> None:
        args = GetInsiderActivityFromIdentifiersArgs(identifiers=["SPGI"])
        assert args.activity_types is None
        assert args.transaction_direction == TransactionDirection.both

    @pytest.mark.parametrize("activity_types", [["disclosures"], ["disclosures", "open_market"]])
    def test_disclosures_with_acquisitions_are_accepted(self, activity_types: list[str]) -> None:
        """Even the combination that matches nothing is accepted; the tool says so in a note."""
        GetInsiderActivityFromIdentifiersArgs(
            identifiers=["SPGI"],
            activity_types=activity_types,
            transaction_direction="acquisitions",
        )

    @pytest.mark.parametrize("activity_types", [[], ["all"], ["open_market_transactions"]])
    def test_rejects_invalid_activity_types(self, activity_types: list[str]) -> None:
        with pytest.raises(ValidationError):
            GetInsiderActivityFromIdentifiersArgs(
                identifiers=["SPGI"], activity_types=activity_types
            )

    def test_removed_params_are_gone(self) -> None:
        fields = GetInsiderActivityFromIdentifiersArgs.model_fields
        for removed in (
            "owner_company_identifiers",
            "activity_type",
            "include_derivatives",
            "include_automatic",
        ):
            assert removed not in fields


class TestGetInsiderActivity:
    @pytest.mark.asyncio
    async def test_default_request_leaves_out_disclosures(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(INSIDER_TRADES_URL, json=DEFAULT_INSIDER_TRADES_PAYLOAD).respond(
            json=insider_trades_response()
        )

        resp = await get_insider_activity_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client
        )

        result = resp.identifier_results["SPGI"]
        assert result.activity[0].trade_date == date(2026, 5, 1)
        assert resp.notes is None
        output = resp.model_dump(mode="json", exclude_none=True)
        assert set(output["results"]["SPGI"]["data"]) == {"activity", "total_matching"}

    @pytest.mark.asyncio
    async def test_filters_are_sent_in_the_request(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(
            INSIDER_TRADES_URL,
            json={
                "company_id": SPGI_COMPANY_ID,
                "sort_by": "absolute_transaction_value_usd",
                "transaction_types": [
                    "open_market_disposition",
                    "open_market_derivative_disposition",
                ],
                "limit": "all",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "owner_ids": [OWNER_COMPANY_ID, PERSON_ID],
                "min_absolute_transaction_value_usd": 1000000.0,
            },
        ).respond(json=insider_trades_response())

        resp = await get_insider_activity_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            activity_types=[InsiderActivityType.open_market],
            transaction_direction=TransactionDirection.dispositions,
            insider_ids=[OWNER_COMPANY_ID, PERSON_ID],
            min_absolute_transaction_value_usd=1000000.0,
            sort_by=InsiderTradesSortBy.absolute_transaction_value_usd,
            limit="all",
        )

        assert "SPGI" in resp.identifier_results

    @pytest.mark.asyncio
    async def test_disclosures_request(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(
            INSIDER_TRADES_URL,
            json={
                **DEFAULT_INSIDER_TRADES_PAYLOAD,
                "transaction_types": ["intent_to_sell_form_144"],
            },
        ).respond(json=insider_trades_response())

        resp = await get_insider_activity_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            activity_types=[InsiderActivityType.disclosures],
            transaction_direction=TransactionDirection.dispositions,
        )

        assert "SPGI" in resp.identifier_results

    @pytest.mark.asyncio
    async def test_disclosed_acquisitions_skip_the_request(
        self, httpx_client: httpx2.AsyncClient
    ) -> None:
        """WHEN nothing can match THEN no request is made (the API rejects an empty
        transaction_types) and a note explains why there are no results."""
        resp = await get_insider_activity_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            activity_types=[InsiderActivityType.disclosures],
            transaction_direction=TransactionDirection.acquisitions,
        )

        assert resp.identifier_results == {}
        assert resp.errors == []
        assert resp.notes is not None
        assert resp.notes[0].startswith(
            "No insider activity can match activity_types=['disclosures'] with "
            "transaction_direction='acquisitions'"
        )

    @pytest.mark.asyncio
    async def test_insider_ids_need_no_resolution(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        """insider_ids are sent as owner_ids as given; only identifiers go through /ids."""
        httpx2_mock.post(
            INSIDER_TRADES_URL, json={**DEFAULT_INSIDER_TRADES_PAYLOAD, "owner_ids": [PERSON_ID]}
        ).respond(json=insider_trades_response())

        resp = await get_insider_activity_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client, insider_ids=[PERSON_ID]
        )

        assert "SPGI" in resp.identifier_results

    @pytest.mark.asyncio
    async def test_truncation_note(
        self, httpx_client: httpx2.AsyncClient, httpx2_mock: Router
    ) -> None:
        httpx2_mock.post(INSIDER_TRADES_URL, json=DEFAULT_INSIDER_TRADES_PAYLOAD).respond(
            json=insider_trades_response(total_matching=1976)
        )

        resp = await get_insider_activity_from_identifiers(
            identifiers=["SPGI"], httpx_client=httpx_client
        )

        assert resp.notes == [
            "SPGI: returned 1 of 1,976 matching records. "
            "Set a higher limit, or 'all' for no limit, to see more."
        ]

    @pytest.mark.asyncio
    async def test_unresolvable_identifier(self, httpx_client: httpx2.AsyncClient) -> None:
        resp = await get_insider_activity_from_identifiers(
            identifiers=["non-existent-company"], httpx_client=httpx_client
        )

        assert resp.identifier_results == {}
        assert len(resp.errors) == 1
