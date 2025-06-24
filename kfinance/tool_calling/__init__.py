from typing import Type

from kfinance.tool_calling.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifier,
)
from kfinance.tool_calling.get_capitalization_from_identifier import GetCapitalizationFromIdentifier
from kfinance.tool_calling.get_competitors_from_identifier import GetCompetitorsFromIdentifier
from kfinance.tool_calling.get_cusip_from_ticker import GetCusipFromTicker
from kfinance.tool_calling.get_earnings import GetEarnings
from kfinance.tool_calling.get_financial_line_item_from_identifier import (
    GetFinancialLineItemFromIdentifier,
)
from kfinance.tool_calling.get_financial_statement_from_identifier import (
    GetFinancialStatementFromIdentifier,
)
from kfinance.tool_calling.get_history_metadata_from_identifier import (
    GetHistoryMetadataFromIdentifier,
)
from kfinance.tool_calling.get_info_from_identifier import GetInfoFromIdentifier
from kfinance.tool_calling.get_isin_from_ticker import GetIsinFromTicker
from kfinance.tool_calling.get_latest import GetLatest
from kfinance.tool_calling.get_latest_earnings import GetLatestEarnings
from kfinance.tool_calling.get_n_quarters_ago import GetNQuartersAgo
from kfinance.tool_calling.get_next_earnings import GetNextEarnings
from kfinance.tool_calling.get_prices_from_identifier import GetPricesFromIdentifier
from kfinance.tool_calling.get_segments_from_identifier import (
    GetSegmentsFromIdentifier,
)
from kfinance.tool_calling.get_transcript import GetTranscript
from kfinance.tool_calling.resolve_identifier import ResolveIdentifier
from kfinance.tool_calling.shared_models import KfinanceTool


ALL_TOOLS: list[Type[KfinanceTool]] = [
    GetLatest,
    GetNQuartersAgo,
    GetIsinFromTicker,
    GetCusipFromTicker,
    GetInfoFromIdentifier,
    GetEarnings,
    GetLatestEarnings,
    GetNextEarnings,
    GetTranscript,
    GetHistoryMetadataFromIdentifier,
    GetPricesFromIdentifier,
    GetCapitalizationFromIdentifier,
    GetFinancialStatementFromIdentifier,
    GetFinancialLineItemFromIdentifier,
    GetBusinessRelationshipFromIdentifier,
    ResolveIdentifier,
    GetSegmentsFromIdentifier,
    GetCompetitorsFromIdentifier,
]
