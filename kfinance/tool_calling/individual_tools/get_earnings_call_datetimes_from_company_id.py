import json
from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class GetEarningsCallDatetimesFromCompanyIdArgs(BaseModel):
    company_id: int


class GetEarningsCallDatetimesFromCompanyId(KfinanceTool):
    name: str = "get_earnings_call_datetimes_from_company_id"
    description: str = "Get earnings call datetimes associated with a company_id."
    args_schema: Type[BaseModel] = GetEarningsCallDatetimesFromCompanyIdArgs
    required_permission: Permission | None = Permission.EarningsPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, company_id: int) -> str:
        company = self.kfinance_client.company(company_id)
        earnings_call_datetimes = company.earnings_call_datetimes
        return json.dumps([dt.isoformat() for dt in earnings_call_datetimes])
