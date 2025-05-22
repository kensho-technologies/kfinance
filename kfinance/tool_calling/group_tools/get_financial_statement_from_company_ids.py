from textwrap import dedent
from typing import Literal, Type

import pandas as pd
from pydantic import BaseModel, Field

from kfinance.constants import PeriodType, Permission, StatementType, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.shared_models import KfinanceTool


class GetFinancialStatementFromCompanyIdsArgs(BaseModel):
    company_ids: list[int]
    # no description because the description for enum fields comes from the enum docstring.
    statement: StatementType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialStatementFromCompanyIds(KfinanceTool):
    name: str = "get_financial_statement_from_company_ids"
    description: str = dedent("""
        Get a financial statement associated with a group of company_ids.

        - To fetch the most recent value for the statement, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "Fetch the balance sheets of companies 6057741 and 874276 for 2024"
        Function: get_financial_statement_from_company_ids(company_ids=[6057741, 874276], statement=StatementType.balance_sheet, start_year=2024, end_year=2024)
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialStatementFromCompanyIdsArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        company_ids: list[int],
        statement: StatementType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict[str, str]:
        companies = Companies(
            kfinance_api_client=self.kfinance_client.kfinance_api_client, company_ids=company_ids
        )

        fetched_results: dict[Company, pd.DataFrame | None] = getattr(companies, statement)(
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

        stringified_results = dict()
        for company, result in fetched_results.items():
            if result is None:
                stringified_result = "unavailable"
            else:
                # If no date and multiple companies, only return the most recent value.
                if start_year == end_year == start_quarter == end_quarter and len(company_ids) > 1:
                    result = result.iloc[:, [-1]]
                stringified_result = str(result.to_dict())
            stringified_results[f"company_id: {company.company_id}"] = stringified_result

        return stringified_results
