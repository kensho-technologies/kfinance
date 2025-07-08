from typing import Type

from kfinance.tool_calling.get_business_relationship_from_identifiers import (
    GetBusinessRelationshipFromIdentifiers,
)
from kfinance.tool_calling.get_capitalization_from_identifiers import (
    GetCapitalizationFromIdentifiers,
)
from kfinance.tool_calling.get_competitors_from_identifiers import GetCompetitorsFromIdentifiers
from kfinance.tool_calling.get_cusip_from_identifiers import GetCusipFromIdentifiers
from kfinance.tool_calling.earnings.get_earnings_from_identifiers import GetEarningsFromIdentifiers

from kfinance.tool_calling.get_financial_line_item_from_identifiers import (
    GetFinancialLineItemFromIdentifiers,
)
from kfinance.tool_calling.get_financial_statement_from_identifiers import (
    GetFinancialStatementFromIdentifiers,
)
from kfinance.tool_calling.get_history_metadata_from_identifiers import (
    GetHistoryMetadataFromIdentifiers,
)
from kfinance.tool_calling.get_history_metadata_from_identifiers import (
    GetHistoryMetadataFromIdentifiers,
)
from kfinance.tool_calling.get_info_from_identifiers import GetInfoFromIdentifiers
from kfinance.tool_calling.get_isin_from_identifiers import GetIsinFromIdentifiers
from kfinance.tool_calling.get_latest import GetLatest
from kfinance.tool_calling.earnings.get_latest_earnings_from_identifiers import GetLatestEarnings
from kfinance.tool_calling.get_n_quarters_ago import GetNQuartersAgo
from kfinance.tool_calling.earnings.get_next_earnings import GetNextEarnings
from kfinance.tool_calling.get_prices_from_identifier import GetPricesFromIdentifier
from kfinance.tool_calling.get_prices_from_identifiers import (
    GetPricesFromIdentifiers,
)
from kfinance.tool_calling.get_segments_from_identifier import (
    GetSegmentsFromIdentifier,
)
from kfinance.tool_calling.get_transcript import GetTranscript
from kfinance.tool_calling.shared_models import KfinanceTool


ALL_TOOLS: list[Type[KfinanceTool]] = [
    GetBusinessRelationshipFromIdentifiers,
    GetCapitalizationFromIdentifiers,
    GetCusipFromIdentifiers,
    GetIsinFromIdentifiers,
    GetFinancialLineItemFromIdentifiers,
    GetFinancialStatementFromIdentifiers,
    GetHistoryMetadataFromIdentifiers,
    GetInfoFromIdentifiers,
    GetLatest,
    GetNQuartersAgo,
    GetEarningsFromIdentifiers,
    GetLatestEarnings,
    GetNextEarnings,
    GetTranscript,
    GetHistoryMetadataFromIdentifiers,
    GetPricesFromIdentifier,
    GetBusinessRelationshipFromIdentifiers,
    GetSegmentsFromIdentifier,
    GetCompetitorsFromIdentifiers,
    GetPricesFromIdentifiers,
]
