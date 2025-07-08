from typing import Type

from kfinance.tool_calling.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifiers,
)
from kfinance.tool_calling.get_capitalization_from_identifiers import (
    GetCapitalizationFromIdentifiers,
)
from kfinance.tool_calling.get_cusip_from_identifiers import GetCusipFromIdentifiers
from kfinance.tool_calling.get_earnings_call_datetimes_from_identifiers import (
    GetEarningsCallDatetimesFromIdentifiers,
)
from kfinance.tool_calling.get_financial_line_item_from_identifiers import (
    GetFinancialLineItemFromIdentifiers,
)
from kfinance.tool_calling.get_financial_statement_from_identifiers import (
    GetFinancialStatementFromIdentifiers,
)
from kfinance.tool_calling.get_history_metadata_from_identifiers import (
    GetHistoryMetadataFromIdentifiers,
)
from kfinance.tool_calling.get_info_from_identifiers import GetInfoFromIdentifiers
from kfinance.tool_calling.get_isin_from_identifiers import GetIsinFromIdentifiers
from kfinance.tool_calling.get_prices_from_identifiers import (
    GetPricesFromIdentifiers,
)
from kfinance.tool_calling.shared_models import KfinanceTool
from kfinance.tool_calling.get_latest import GetLatest
from kfinance.tool_calling.get_n_quarters_ago import GetNQuartersAgo


ALL_TOOLS: list[Type[KfinanceTool]] = [
    GetBusinessRelationshipFromIdentifiers,
    GetCapitalizationFromIdentifiers,
    GetEarningsCallDatetimesFromIdentifiers,
    GetCusipFromIdentifiers,
    GetIsinFromIdentifiers,
    GetFinancialLineItemFromIdentifiers,
    GetFinancialStatementFromIdentifiers,
    GetHistoryMetadataFromIdentifiers,
    GetInfoFromIdentifiers,
    GetLatest,
    GetNQuartersAgo,
    GetPricesFromIdentifiers,
]
