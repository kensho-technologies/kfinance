from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.shared_models import KfinanceTool


class GetInfoFromCompanyIdsArgs(BaseModel):
    company_ids: list[int]


class GetInfoFromCompanyIds(KfinanceTool):
    name: str = "get_info_from_company_ids"
    description: str = dedent("""
        Get the information associated with an company_id. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = GetInfoFromCompanyIdsArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, company_ids: list[int]) -> dict[str, str | dict]:
        companies = Companies(
            kfinance_api_client=self.kfinance_client.kfinance_api_client, company_ids=company_ids
        )

        fetched_results: dict[Company, dict | None] = companies.info  # type:ignore[attr-defined]

        stringified_results = dict()
        for company, result in fetched_results.items():
            stringified_result = "unavailable" if result is None else result
            stringified_results[f"company_id: {company.company_id}"] = stringified_result

        return stringified_results
