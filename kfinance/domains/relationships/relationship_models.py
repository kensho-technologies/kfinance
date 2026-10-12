from pydantic import BaseModel
from strenum import StrEnum

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


# The relationship types served by the Business Relationships dataset.
class BusinessRelationshipType(StrEnum):
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


# The relationship types served by the Company Relationships dataset.
class CompanyRelationshipType(StrEnum):
    """The type of relationship"""

    creditor = "creditor"
    borrower = "borrower"
    fund_distributor = "fund_distributor"
    distributed_fund = "distributed_fund"
    fund_family = "fund_family"
    fund_family_member = "fund_family_member"
    fund_investment_advisor = "fund_investment_advisor"
    advised_fund = "advised_fund"
    fund_sponsor = "fund_sponsor"
    sponsored_fund = "sponsored_fund"


AnyRelationshipType = RelationshipType | BusinessRelationshipType | CompanyRelationshipType


class RelationshipResponse(BaseModel):
    """A response from the relationship endpoint that includes both company_id and name."""

    current: list[CompanyIdAndName]
    previous: list[CompanyIdAndName]
    # The API may omit these keys entirely depending on client entitlements
    pending: list[CompanyIdAndName] | None = None
    cancelled: list[CompanyIdAndName] | None = None
