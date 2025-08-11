from kfinance.domains.business_relationships.business_relationship_tools import (
    GetBusinessRelationshipFromIdentifiers,
)
from kfinance.domains.capitalizations.capitalization_tools import GetCapitalizationFromIdentifiers
from kfinance.domains.companies.company_tools import GetInfoFromIdentifiers
from kfinance.domains.competitors.competitor_tools import GetCompetitorsFromIdentifiers
from kfinance.domains.cusip_and_isin.cusip_and_isin_tools import (
    GetCusipFromIdentifiers,
    GetIsinFromIdentifiers,
)
from kfinance.domains.earnings.earning_tools import (
    GetEarningsFromIdentifiers,
    GetLatestEarningsFromIdentifiers,
    GetNextEarningsFromIdentifiers,
    GetTranscriptFromKeyDevId,
)
from kfinance.domains.line_items.line_item_tools import GetFinancialLineItemFromIdentifiers
from kfinance.domains.prices.price_tools import GetPricesFromIdentifiers
from kfinance.domains.segments.segment_tools import GetSegmentsFromIdentifiers
from kfinance.domains.statements.statement_tools import GetFinancialStatementFromIdentifiers
from kfinance.integrations.tool_calling.static_tools.get_latest import GetLatest
from kfinance.integrations.tool_calling.static_tools.get_n_quarters_ago import GetNQuartersAgo
from kfinance.integrations.tool_calling.tool_calling_models import KfinanceTool


# A list of all available tools
ALL_TOOLS: list[type[KfinanceTool]] = [
    # Static / no API call tools
    GetLatest,
    GetNQuartersAgo,
    # Business Relationships
    GetBusinessRelationshipFromIdentifiers,
    # Capitalizations
    GetCapitalizationFromIdentifiers,
    # Companies
    GetInfoFromIdentifiers,
    # Competitors
    GetCompetitorsFromIdentifiers,
    # Cusip and Isin
    GetCusipFromIdentifiers,
    GetIsinFromIdentifiers,
    # Earnings
    GetEarningsFromIdentifiers,
    GetLatestEarningsFromIdentifiers,
    GetNextEarningsFromIdentifiers,
    GetTranscriptFromKeyDevId,
    # Line Items
    GetFinancialLineItemFromIdentifiers,
    # Prices
    GetPricesFromIdentifiers,
    # Segments
    GetSegmentsFromIdentifiers,
    # Statements
    GetFinancialStatementFromIdentifiers,
]
