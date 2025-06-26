from typing import Type

from kfinance.tool_calling.group_tools.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifiers,
)
from kfinance.tool_calling.group_tools.get_capitalization_from_identifiers import (
    GetCapitalizationFromIdentifiers,
)
from kfinance.tool_calling.group_tools.get_cusip_from_identifiers import GetCusipFromIdentifiers
from kfinance.tool_calling.group_tools.get_earnings_call_datetimes_from_identifiers import (
    GetEarningsCallDatetimesFromIdentifiers,
)
from kfinance.tool_calling.group_tools.get_financial_line_item_from_identifiers import (
    GetFinancialLineItemFromIdentifiers,
)
from kfinance.tool_calling.group_tools.get_financial_statement_from_identifiers import (
    GetFinancialStatementFromIdentifiers,
)
from kfinance.tool_calling.group_tools.get_history_metadata_from_identifiers import (
    GetHistoryMetadataFromIdentifiers,
)
from kfinance.tool_calling.group_tools.get_info_from_identifiers import GetInfoFromIdentifiers
from kfinance.tool_calling.group_tools.get_isin_from_identifiers import GetIsinFromIdentifiers
from kfinance.tool_calling.group_tools.get_prices_from_identifiers import (
    GetPricesFromIdentifiers,
)
from kfinance.tool_calling.individual_tools.get_capitalization_from_identifier import GetCapitalizationFromIdentifier
from kfinance.tool_calling.individual_tools.get_cusip_from_identifier import GetCusipFromIdentifier
from kfinance.tool_calling.individual_tools.get_earnings_call_datetimes_from_identifier import \
    GetEarningsCallDatetimesFromIdentifier
from kfinance.tool_calling.individual_tools.get_financial_line_item_from_identifier import \
    GetFinancialLineItemFromIdentifier
from kfinance.tool_calling.individual_tools.get_financial_statement_from_identifier import \
    GetFinancialStatementFromIdentifier
from kfinance.tool_calling.individual_tools.get_history_metadata_from_identifier import GetHistoryMetadataFromIdentifier
from kfinance.tool_calling.individual_tools.get_info_from_identifier import GetInfoFromIdentifier
from kfinance.tool_calling.individual_tools.get_isin_from_identifier import GetIsinFromIdentifier
from kfinance.tool_calling.individual_tools.get_prices_from_identifier import GetPricesFromIdentifier
from kfinance.tool_calling.shared_models import KfinanceTool
from kfinance.tool_calling.shared_tools.get_latest import GetLatest
from kfinance.tool_calling.shared_tools.get_n_quarters_ago import GetNQuartersAgo


ALL_TOOLS: list[Type[KfinanceTool]] = [
    # Shared
    GetLatest,
    GetNQuartersAgo,
    # Individual
    GetIsinFromIdentifier,
    GetCusipFromIdentifier,
    GetInfoFromIdentifier,
    GetEarningsCallDatetimesFromIdentifier,
    GetHistoryMetadataFromIdentifier,
    GetPricesFromIdentifier,
    GetCapitalizationFromIdentifier,
    GetFinancialStatementFromIdentifier,
    GetFinancialLineItemFromIdentifier,
    # Group
    GetBusinessRelationshipFromIdentifiers,
    GetCapitalizationFromIdentifiers,
    GetEarningsCallDatetimesFromIdentifiers,
    GetCusipFromIdentifiers,
    GetIsinFromIdentifiers,
    GetFinancialLineItemFromIdentifiers,
    GetFinancialStatementFromIdentifiers,
    GetHistoryMetadataFromIdentifiers,
    GetInfoFromIdentifiers,
    GetPricesFromIdentifiers,
]
