import httpx2
from pydantic import BaseModel, ValidationError
import pytest
from strenum import StrEnum

from kfinance.conftest import SPGI_ID_TRIPLE
from kfinance.domains.companies.company_models import CompanyIdAndName
from kfinance.domains.relationships.relationship_models import (
    BusinessRelationshipType,
    CompanyRelationshipType,
    RelationshipResponse,
    RelationshipType,
)
from kfinance.domains.relationships.relationship_tools import (
    GetBusinessRelationshipFromIdentifiersArgs,
    GetCompanyRelationshipFromIdentifiersArgs,
    GetRelationshipFromIdentifiersResp,
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


class TestRelationshipTypeEnums:
    def test_dataset_enums_partition_relationship_type(self) -> None:
        """The two dataset enums together cover RelationshipType."""
        business = {relationship_type.value for relationship_type in BusinessRelationshipType}
        company = {relationship_type.value for relationship_type in CompanyRelationshipType}

        assert business | company == {
            relationship_type.value for relationship_type in RelationshipType
        }
        assert business & company == {"creditor", "borrower"}

    @pytest.mark.parametrize(
        "args_model, expected_enum, valid_value, invalid_value",
        [
            pytest.param(
                GetBusinessRelationshipFromIdentifiersArgs,
                BusinessRelationshipType,
                "supplier",
                "sponsored_fund",
                id="business relationships only",
            ),
            pytest.param(
                GetCompanyRelationshipFromIdentifiersArgs,
                CompanyRelationshipType,
                "sponsored_fund",
                "supplier",
                id="company relationships only",
            ),
        ],
    )
    def test_dataset_args_models_restrict_relationship_type(
        self,
        args_model: type[BaseModel],
        expected_enum: type[StrEnum],
        valid_value: str,
        invalid_value: str,
    ) -> None:
        """
        GIVEN an args model for a single dataset
        WHEN we inspect its json schema and validate a relationship type
        THEN only that dataset's types are advertised and accepted.
        """
        schema = args_model.model_json_schema()
        (relationship_type_def,) = (
            definition
            for name, definition in schema["$defs"].items()
            if name.endswith("RelationshipType")
        )
        assert set(relationship_type_def["enum"]) == {
            relationship_type.value for relationship_type in expected_enum
        }
        # The enum docstring is what pydantic emits as the parameter description.
        assert relationship_type_def["description"] == "The type of relationship"
        # creditor and borrower live in both datasets, so they stay available.
        assert {"creditor", "borrower"} <= set(relationship_type_def["enum"])

        args = args_model.model_validate(
            {"identifiers": ["SPGI"], "relationship_type": valid_value}
        )
        assert args.model_dump(mode="json")["relationship_type"] == valid_value

        with pytest.raises(ValidationError):
            args_model.model_validate({"identifiers": ["SPGI"], "relationship_type": invalid_value})
