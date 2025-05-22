from datetime import date

from pydantic import BaseModel, Field

from kfinance.constants import Capitalization, Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCapitalizationFromCompanyIdArgs(BaseModel):
    # no description because the description for enum fields comes from the enum docstring.
    company_id: int
    capitalization: Capitalization
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval", default=None
    )


class GetCapitalizationFromCompanyId(KfinanceTool):
    name: str = "get_capitalization_from_company_id"
    description: str = "Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for a company_id between inclusive start_date and inclusive end date. When requesting the most recent values, leave start_date and end_date empty."
    args_schema = GetCapitalizationFromCompanyIdArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(
        self,
        company_id: int,
        capitalization: Capitalization,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        company = self.kfinance_client.company(company_id)
        return getattr(company, capitalization.value)(
            start_date=start_date, end_date=end_date
        ).to_markdown()
