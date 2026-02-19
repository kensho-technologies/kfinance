from kfinance.domains.business_relationships.business_relationship_tools import (
    GetBusinessRelationshipFromIdentifiers,
)
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


# A list of all available tools
ALL_TOOLS: list[type[KfinanceTool]] = [
    # # Static / no API call tools
    # GetLatest,
    # GetNQuartersAgo,
    # # Business Relationships
    GetBusinessRelationshipFromIdentifiers,
    # # Capitalizations
    # GetCapitalizationFromIdentifiers,
    # # Companies
    # GetInfoFromIdentifiers,
    # GetCompanyOtherNamesFromIdentifiers,
    # GetCompanySummaryFromIdentifiers,
    # GetCompanyDescriptionFromIdentifiers,
    # # Competitors
    # GetCompetitorsFromIdentifiers,
    # # Cusip and Isin
    # GetCusipFromIdentifiers,
    # GetIsinFromIdentifiers,
    # # Earnings
    # GetEarningsFromIdentifiers,
    # GetLatestEarningsFromIdentifiers,
    # GetNextEarningsFromIdentifiers,
    # GetTranscriptFromKeyDevId,
    # # Line Items
    # GetFinancialLineItemFromIdentifiers,
    # # Prices
    # GetPricesFromIdentifiers,
    # GetHistoryMetadataFromIdentifiers,
    # # Segments
    # GetSegmentsFromIdentifiers,
    # # Statements
    # GetFinancialStatementFromIdentifiers,
    # # Mergers & Acquisitions
    # GetAdvisorsForCompanyInTransactionFromIdentifier,
    # GetMergerInfoFromTransactionId,
    # GetMergersFromIdentifiers,
    # # Rounds of Funding
    # GetRoundsOfFundingFromIdentifiers,
    # GetRoundsOfFundingInfoFromTransactionIds,
    # GetFundingSummaryFromIdentifiers,
    # # Estimates
    # GetConsensusEstimatesFromIdentifiers,
    # GetGuidanceFromIdentifiers,
]
