from textwrap import dedent
from typing import Literal, Type

import pandas as pd
from pydantic import BaseModel, Field

from kfinance.constants import LINE_ITEM_NAMES_AND_ALIASES, PeriodType, Permission, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.shared_models import KfinanceTool


class GetFinancialLineItemFromCompanyIdsArgs(BaseModel):
    company_ids: list[int]
    # Note: mypy will not enforce this literal because of the type: ignore.
    # But pydantic still uses the literal to check for allowed values and only includes
    # allowed values in generated schemas.
    line_item: Literal[tuple(LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of financial line_item requested"
    )
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialLineItemFromCompanyIds(KfinanceTool):
    name: str = "get_financial_line_item_from_company_ids"
    description: str = dedent("""
        Get the financial line item associated with a company_id.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.
        - To fetch the most recent value for the line item, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "What are the revenues of companies 6057741 and 874276?"
        Function: get_line_item(line_item="revenue", company_ids=[6057741, 874276])
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialLineItemFromCompanyIdsArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        company_ids: list[int],
        line_item: str,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict[str, str]:
        companies = Companies(
            kfinance_api_client=self.kfinance_client.kfinance_api_client, company_ids=company_ids
        )

        fetched_results: dict[Company, pd.DataFrame | None] = getattr(companies, line_item)(
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

        stringified_results = dict()
        for company, result in fetched_results.items():
            if result is None or (isinstance(result, pd.DataFrame) and result.empty):
                stringified_result = "unavailable"
            else:
                # If no date and multiple companies, only return the most recent value.
                if start_year == end_year == start_quarter == end_quarter and len(company_ids) > 1:
                    result = result.iloc[:, [-1]]
                stringified_result = str(result.to_dict())
            stringified_results[f"company_id: {company.company_id}"] = stringified_result

        return stringified_results
