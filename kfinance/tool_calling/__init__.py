from typing import Type

from kfinance.tool_calling.get_business_relationship_from_identifier import (
    GetBusinessRelationshipFromIdentifier,
)
from kfinance.tool_calling.get_capitalization_from_identifier import GetCapitalizationFromIdentifier
from kfinance.tool_calling.get_company_id_from_identifier import GetCompanyIdFromIdentifier
from kfinance.tool_calling.get_cusip_from_ticker import GetCusipFromTicker
from kfinance.tool_calling.get_earnings_call_datetimes_from_identifier import (
    GetEarningsCallDatetimesFromIdentifier,
)
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
from kfinance.tool_calling.get_n_quarters_ago import GetNQuartersAgo
from kfinance.tool_calling.get_prices_from_identifier import GetPricesFromIdentifier
from kfinance.tool_calling.get_security_id_from_identifier import GetSecurityIdFromIdentifier
from kfinance.tool_calling.get_trading_item_id_from_identifier import GetTradingItemIdFromIdentifier
from kfinance.tool_calling.shared_models import KfinanceTool


ALL_TOOLS: list[Type[KfinanceTool]] = [
    GetLatest,
    GetNQuartersAgo,
    GetCompanyIdFromIdentifier,
    GetSecurityIdFromIdentifier,
    GetTradingItemIdFromIdentifier,
    GetIsinFromTicker,
    GetCusipFromTicker,
    GetInfoFromIdentifier,
    GetEarningsCallDatetimesFromIdentifier,
    GetHistoryMetadataFromIdentifier,
    GetPricesFromIdentifier,
    GetCapitalizationFromIdentifier,
    GetFinancialStatementFromIdentifier,
    GetFinancialLineItemFromIdentifier,
    GetBusinessRelationshipFromIdentifier,
]
