from strenum import StrEnum


class BusinessRelationshipType(StrEnum):
    """The type of business relationship"""

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
