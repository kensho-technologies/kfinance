from datetime import datetime
from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.shared_models import KfinanceTool


class GetEarningsCallDatetimesFromCompanyIdsArgs(BaseModel):
    company_ids: list[int]


class GetEarningsCallDatetimesFromCompanyIds(KfinanceTool):
    name: str = "get_earnings_call_datetimes_from_company_ids"
    description: str = dedent("""
        Get earnings call datetimes associated with a list of company_ids.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.

        Example:
        Query: "What were the earnings call datetimes of companies 6057741 and 874276?"
        Function: get_earnings_call_datetimes_from_company_ids(company_ids=[6057741, 874276])
    """).strip()
    args_schema: Type[BaseModel] = GetEarningsCallDatetimesFromCompanyIdsArgs
    required_permission: Permission | None = Permission.EarningsPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, company_ids: list[int]) -> dict[str, list[str]]:
        companies = Companies(
            kfinance_api_client=self.kfinance_client.kfinance_api_client, company_ids=company_ids
        )

        fetched_results: dict[Company, list[datetime]] = companies.earnings_call_datetimes  # type:ignore[attr-defined]
        stringified_results = dict()
        for company, result in fetched_results.items():
            stringified_result = [dt.isoformat() for dt in result]
            stringified_results[f"company_id: {company.company_id}"] = stringified_result
        return stringified_results
