from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.constants import PeriodType, Permission, StatementType, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class GetFinancialStatementFromCompanyIdArgs(BaseModel):
    company_id: int
    # no description because the description for enum fields comes from the enum docstring.
    statement: StatementType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialStatementFromCompanyId(KfinanceTool):
    name: str = "get_financial_statement_from_company_id"
    description: str = "Get the financial statement associated with a company_id."
    args_schema: Type[BaseModel] = GetFinancialStatementFromCompanyIdArgs
    required_permission: Permission | None = Permission.StatementsPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(
        self,
        company_id: int,
        statement: StatementType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> str:
        company = self.kfinance_client.company(company_id)
        return getattr(company, statement.value)(
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        ).to_markdown()
