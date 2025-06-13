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
    ResolveIdentifier,
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
