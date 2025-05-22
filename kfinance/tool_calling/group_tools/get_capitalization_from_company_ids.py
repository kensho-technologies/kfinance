from datetime import date
from textwrap import dedent

import pandas as pd
from pydantic import BaseModel, Field

from kfinance.constants import Capitalization, Permission, ToolMode
from kfinance.kfinance import Companies, Company
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCapitalizationFromCompanyIdsArgs(BaseModel):
    # no description because the description for enum fields comes from the enum docstring.
    company_ids: list[int]
    capitalization: Capitalization
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval", default=None
    )


class GetCapitalizationFromCompanyIds(KfinanceTool):
    name: str = "get_capitalization_from_company_ids"
    description: str = dedent("""
        Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for a group of company_ids between inclusive start_date and inclusive end date.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the market caps of companies 6057741 and 874276?"
        Function: get_capitalization(capitalization=Capitalization.market_cap, company_ids=[6057741, 874276])
    """).strip()
    args_schema = GetCapitalizationFromCompanyIdsArgs
    required_permission: Permission | None = Permission.PricingPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        company_ids: list[int],
        capitalization: Capitalization,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, str]:
        companies = Companies(
            kfinance_api_client=self.kfinance_client.kfinance_api_client, company_ids=company_ids
        )

        fetched_results: dict[Company, pd.DataFrame] = getattr(companies, capitalization.value)(
            start_date=start_date, end_date=end_date
        )

        stringified_results = dict()
        for company, result in fetched_results.items():
            if start_date == end_date is None and len(companies) > 1:
                # If more than one company was passed without start and end date,
                # assume that the caller only cares about the last known value
                stringified_result = str(result.tail(1).to_dict())
            else:
                stringified_result = result.to_markdown()
            stringified_results[f"company_id: {company.company_id}"] = stringified_result

        return stringified_results
