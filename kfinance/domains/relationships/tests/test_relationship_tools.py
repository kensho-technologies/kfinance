import httpx2
import pytest

from kfinance.client.permission_models import Permission
from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import CompanyIdAndName
from kfinance.domains.relationships.relationship_models import (
    CR_ONLY_RELATIONSHIP_TYPES,
    RelationshipResponse,
    RelationshipType,
    permitted_relationship_types,
)
from kfinance.domains.relationships.relationship_tools import (
    GetRelationshipFromIdentifiersResp,
    build_relationship_args_model,
    fetch_relationship_from_company_id,
    get_relationship_from_identifiers,
)


class TestRelationships:
    expected_spgi_relationship_response = RelationshipResponse(
        current=[CompanyIdAndName(company_id=883103, company_name="CRISIL Limited")],
        previous=[
            CompanyIdAndName(company_id=472898, company_name="Morgan Stanley"),
            CompanyIdAndName(company_id=8182358, company_name="Eloqua, Inc."),
        ],
    )

    @pytest.mark.asyncio
    async def test_fetch_relationship_from_company_id(
        self, httpx_client: httpx2.AsyncClient, add_spgi_supplier_mock_resp: None
    ) -> None:
        """
        WHEN we fetch SPGI's supplier using SPGI's company id
        THEN we get back a RelationshipResponse with SPGI's suppliers.
        """

        resp = await fetch_relationship_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            relationship_type=RelationshipType.supplier,
            httpx_client=httpx_client,
        )

        assert resp == self.expected_spgi_relationship_response

    @pytest.mark.asyncio
    async def test_get_relationship_from_identifiers(
        self, httpx_client: httpx2.AsyncClient, add_spgi_supplier_mock_resp: None
    ) -> None:
        """
        WHEN we fetch suppliers for SPGI and a non-existent company
        THEN we get back SPGI's suppliers and an error for the non-existent company.
        """

        expected_resp = GetRelationshipFromIdentifiersResp(
            relationship_type=RelationshipType.supplier,
            identifier_results={"SPGI": self.expected_spgi_relationship_response},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        resp = await get_relationship_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            relationship_type=RelationshipType.supplier,
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_relationship_omits_absent_statuses(
        self, httpx_client: httpx2.AsyncClient, add_spgi_supplier_mock_resp: None
    ) -> None:
        """
        GIVEN a response without the Company Relationships-only statuses
        WHEN we serialize the tool response
        THEN "pending" and "cancelled" are absent rather than empty.
        """

        resp = await get_relationship_from_identifiers(
            identifiers=["SPGI"],
            relationship_type=RelationshipType.supplier,
            httpx_client=httpx_client,
        )

        dumped = resp.model_dump(mode="json", exclude_none=True)
        assert set(dumped["results"]["SPGI"]["data"]) == {"current", "previous"}

    @pytest.mark.asyncio
    async def test_get_relationship_includes_cr_only_statuses(
        self, httpx_client: httpx2.AsyncClient, add_spgi_sponsored_fund_mock_resp: None
    ) -> None:
        """
        GIVEN a fund relationship response that includes all four statuses
        WHEN we fetch that relationship
        THEN "pending" and "cancelled" are surfaced alongside "current" and "previous".
        """

        resp = await get_relationship_from_identifiers(
            identifiers=["SPGI"],
            relationship_type=RelationshipType.sponsored_fund,
            httpx_client=httpx_client,
        )

        dumped = resp.model_dump(mode="json", exclude_none=True)
        assert dumped["results"]["SPGI"]["data"] == {
            "current": [{"company_id": "C_1", "company_name": "Company 1"}],
            "previous": [{"company_id": "C_2", "company_name": "Company 2"}],
            "pending": [{"company_id": "C_3", "company_name": "Company 3"}],
            "cancelled": [{"company_id": "C_4", "company_name": "Company 4"}],
        }


class TestRelationshipTypePermissions:
    @pytest.mark.parametrize(
        "permissions, expects_cr_only_types",
        [
            pytest.param({Permission.RelationshipPermission}, False, id="relationship only"),
            pytest.param(
                {Permission.RelationshipPermission, Permission.OnlyStaffPermission},
                True,
                id="relationship and staff",
            ),
        ],
    )
    def test_permitted_relationship_types(
        self, permissions: set[Permission], expects_cr_only_types: bool
    ) -> None:
        """
        GIVEN a set of user permissions
        WHEN we compute the permitted relationship types
        THEN the Company Relationships-only types are included only for entitled users.
        """
        permitted = permitted_relationship_types(permissions)

        if expects_cr_only_types:
            assert permitted == frozenset(RelationshipType)
        else:
            assert permitted == frozenset(RelationshipType) - CR_ONLY_RELATIONSHIP_TYPES
            assert not permitted & CR_ONLY_RELATIONSHIP_TYPES
            # creditor and borrower live in both datasets, so they stay available.
            assert {RelationshipType.creditor, RelationshipType.borrower} <= permitted

    def test_build_relationship_args_model_restricts_enum(self) -> None:
        """
        WHEN we build an args model from a restricted set of relationship types
        THEN only those values validate, and the json schema only advertises those values.
        """
        permitted = permitted_relationship_types({Permission.RelationshipPermission})
        args_model = build_relationship_args_model(permitted)

        schema = args_model.model_json_schema()
        enum_values = set(schema["$defs"]["RelationshipType"]["enum"])
        assert enum_values == {t.value for t in permitted}
        assert "sponsored_fund" not in enum_values

        args = args_model.model_validate({"identifiers": ["SPGI"], "relationship_type": "supplier"})
        assert args.relationship_type == RelationshipType.supplier

        with pytest.raises(ValueError):
            args_model.model_validate(
                {"identifiers": ["SPGI"], "relationship_type": "sponsored_fund"}
            )

    def test_build_relationship_args_model_is_cached(self) -> None:
        """Equal permitted sets reuse the same generated model."""
        permitted = permitted_relationship_types({Permission.RelationshipPermission})
        assert build_relationship_args_model(permitted) is build_relationship_args_model(
            frozenset(permitted)
        )
