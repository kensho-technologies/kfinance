from typing import Type

from kfinance.tool_calling.group_tools.filter_companies import FilterCompanies
from kfinance.tool_calling.group_tools.get_business_relationship_from_company_id import (
    GetBusinessRelationshipFromCompanyId,
)
from kfinance.tool_calling.group_tools.get_capitalization_from_company_ids import (
    GetCapitalizationFromCompanyIds,
)
from kfinance.tool_calling.group_tools.get_cusip_from_security_ids import GetCusipFromSecurityIds
from kfinance.tool_calling.group_tools.get_earnings_call_datetimes_from_company_ids import (
    GetEarningsCallDatetimesFromCompanyIds,
)
from kfinance.tool_calling.group_tools.get_financial_line_item_from_company_ids import (
    GetFinancialLineItemFromCompanyIds,
)
from kfinance.tool_calling.group_tools.get_financial_statement_from_company_ids import (
    GetFinancialStatementFromCompanyIds,
)
from kfinance.tool_calling.group_tools.get_history_metadata_from_trading_item_ids import (
    GetHistoryMetadataFromTradingItemIds,
)
from kfinance.tool_calling.group_tools.get_info_from_company_ids import GetInfoFromCompanyIds
from kfinance.tool_calling.group_tools.get_isin_from_security_ids import GetIsinFromSecurityIds
from kfinance.tool_calling.group_tools.get_prices_from_trading_item_ids import (
    GetPricesFromTradingItemIds,
)
from kfinance.tool_calling.group_tools.resolve_identifiers import ResolveIdentifiers
from kfinance.tool_calling.individual_tools.get_capitalization_from_company_id import (
    GetCapitalizationFromCompanyId,
)
from kfinance.tool_calling.individual_tools.get_cusip_from_security_id import GetCusipFromSecurityId
from kfinance.tool_calling.individual_tools.get_earnings_call_datetimes_from_company_id import (
    GetEarningsCallDatetimesFromCompanyId,
)
from kfinance.tool_calling.individual_tools.get_financial_line_item_from_company_id import (
    GetFinancialLineItemFromCompanyId,
)
from kfinance.tool_calling.individual_tools.get_financial_statement_from_company_id import (
    GetFinancialStatementFromCompanyId,
)
from kfinance.tool_calling.individual_tools.get_history_metadata_from_trading_item_id import (
    GetHistoryMetadataFromTradingItemId,
)
from kfinance.tool_calling.individual_tools.get_info_from_company_id import GetInfoFromCompanyId
from kfinance.tool_calling.individual_tools.get_isin_from_security_id import GetIsinFromSecurityId
from kfinance.tool_calling.individual_tools.get_prices_from_trading_item_id import (
    GetPricesFromTradingItemId,
)
from kfinance.tool_calling.individual_tools.resolve_identifier import ResolveIdentifier
from kfinance.tool_calling.shared_models import KfinanceTool
from kfinance.tool_calling.shared_tools.get_latest import GetLatest
from kfinance.tool_calling.shared_tools.get_n_quarters_ago import GetNQuartersAgo


ALL_TOOLS: list[Type[KfinanceTool]] = [
    # Shared
    GetLatest,
    GetNQuartersAgo,
    # Individual
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
    # Group
    ResolveIdentifiers,
    GetCapitalizationFromCompanyIds,
    GetEarningsCallDatetimesFromCompanyIds,
    GetCusipFromSecurityIds,
    GetIsinFromSecurityIds,
    GetFinancialLineItemFromCompanyIds,
    GetFinancialStatementFromCompanyIds,
    GetHistoryMetadataFromTradingItemIds,
    GetInfoFromCompanyIds,
    GetPricesFromTradingItemIds,
    FilterCompanies,
]
