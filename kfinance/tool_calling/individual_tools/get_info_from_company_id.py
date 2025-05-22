from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class GetInfoFromCompanyIdArgs(BaseModel):
    company_id: int


class GetInfoFromCompanyId(KfinanceTool):
    name: str = "get_info_from_company_id"
    description: str = "Get the information associated with an company_id. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code."
    args_schema: Type[BaseModel] = GetInfoFromCompanyIdArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, company_id: int) -> str:
        return str(self.kfinance_client.company(company_id).info)
