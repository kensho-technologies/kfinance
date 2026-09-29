from pydantic import BaseModel
from strenum import StrEnum

from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_models import CompanyIdAndName


class RelationshipType(StrEnum):
    """The type of relationship"""

    supplier = "supplier"
    customer = "customer"
    distributor = "distributor"
    franchisor = "franchisor"
    franchisee = "franchisee"
    landlord = "landlord"
    tenant = "tenant"
    licensor = "licensor"
    licensee = "licensee"
    creditor = "creditor"
    borrower = "borrower"
    lessor = "lessor"
    lessee = "lessee"
    strategic_alliance = "strategic_alliance"
    investor_relations_firm = "investor_relations_firm"
    investor_relations_client = "investor_relations_client"
    transfer_agent = "transfer_agent"
    transfer_agent_client = "transfer_agent_client"
    vendor = "vendor"
    client_services = "client_services"
    fund_distributor = "fund_distributor"
    distributed_fund = "distributed_fund"
    fund_family = "fund_family"
    fund_family_member = "fund_family_member"
    fund_investment_advisor = "fund_investment_advisor"
    advised_fund = "advised_fund"
    fund_sponsor = "fund_sponsor"
    sponsored_fund = "sponsored_fund"


# Relationship types that require Company Relationships entitlement.
CR_ONLY_RELATIONSHIP_TYPES: frozenset[RelationshipType] = frozenset(
    {
        RelationshipType.fund_distributor,
        RelationshipType.distributed_fund,
        RelationshipType.fund_family,
        RelationshipType.fund_family_member,
        RelationshipType.fund_investment_advisor,
        RelationshipType.advised_fund,
        RelationshipType.fund_sponsor,
        RelationshipType.sponsored_fund,
    }
)

# TODO(LRA-460): point these at the dedicated entitlement once the backend defines it.
RELATIONSHIP_TYPE_PERMISSIONS: dict[RelationshipType, Permission] = {
    relationship_type: Permission.OnlyStaffPermission
    for relationship_type in CR_ONLY_RELATIONSHIP_TYPES
}


def permitted_relationship_types(permissions: set[Permission]) -> frozenset[RelationshipType]:
    """Return the relationship types that a client holding `permissions` may query."""
    return frozenset(
        relationship_type
        for relationship_type in RelationshipType
        if (required := RELATIONSHIP_TYPE_PERMISSIONS.get(relationship_type)) is None
        or required in permissions
    )


class RelationshipResponse(BaseModel):
    """A response from the relationship endpoint that includes both company_id and name."""

    current: list[CompanyIdAndName]
    previous: list[CompanyIdAndName]
    # The API may omit these keys entirely depending on client entitlements
    pending: list[CompanyIdAndName] | None = None
    cancelled: list[CompanyIdAndName] | None = None
