from typing import Type

from tool_calling.non_screener_tools.resolve_identifier import ResolveIdentifier
from kfinance.tool_calling.shared_models import KfinanceTool
from tool_calling.non_screener_tools.get_capitalization_from_company_id import (
    GetCapitalizationFromCompanyId,
)
from tool_calling.non_screener_tools.get_cusip_from_security_id import GetCusipFromSecurityId
from tool_calling.non_screener_tools.get_earnings_call_datetimes_from_company_id import (
    GetEarningsCallDatetimesFromCompanyId,
)
from tool_calling.non_screener_tools.get_financial_line_item_from_company_id import (
    GetFinancialLineItemFromCompanyId,
)
from tool_calling.non_screener_tools.get_financial_statement_from_company_id import (
    GetFinancialStatementFromCompanyId,
)
from tool_calling.non_screener_tools.get_history_metadata_from_trading_item_id import (
    GetHistoryMetadataFromTradingItemId,
)
from tool_calling.non_screener_tools.get_info_from_company_id import GetInfoFromCompanyId
from tool_calling.non_screener_tools.get_isin_from_security_id import GetIsinFromSecurityId
from tool_calling.non_screener_tools.get_prices_from_trading_item_id import \
    GetPricesFromTradingItemId
from tool_calling.screener_tools.get_business_relationship_from_company_id import (
    GetBusinessRelationshipFromCompanyId,
)
from tool_calling.shared_tools.get_latest import GetLatest
from tool_calling.shared_tools.get_n_quarters_ago import GetNQuartersAgo

ALL_TOOLS: list[Type[KfinanceTool]] = [
    GetLatest,
    GetNQuartersAgo,
    GetIsinFromSecurityId,
    GetCusipFromSecurityId,
    GetInfoFromCompanyId,
    GetEarningsCallDatetimesFromCompanyId,
    GetHistoryMetadataFromTradingItemId,
    GetPricesFromTradingItemId,
    GetCapitalizationFromCompanyId,
    GetFinancialStatementFromCompanyId,
    GetFinancialLineItemFromCompanyId,
    GetBusinessRelationshipFromCompanyId,
    ResolveIdentifier,
]
