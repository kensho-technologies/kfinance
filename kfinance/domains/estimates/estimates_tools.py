from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import (
    EstimateType,
    EstimatePeriodType,
    NumPeriodsBackward,
    NumPeriodsForward,
)
from kfinance.client.permission_models import Permission
from kfinance.domains.estimates.estimates_models import EstimatesResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)

class GetEstimatesFromIdentifierArgs(ToolArgsWithIdentifiers):
    estimate_type: EstimateType
    period_type: EstimatePeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")
    num_periods_forward: NumPeriodsForward | None = Field(
        default=None, description="The number of periods in the future to retrieve estimate data."
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None, description="The number of periods in the past to retrieve estimate data.",
    )


class GetEstimatesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EstimatesResp]  # identifier -> response


class GetEstimatesFromIdentifiers(KfinanceTool):
    name: str = "get_estimates_from_identifiers"
    description: str = dedent("""
        meow meow meow meow meow
    """).strip()
    args_schema: Type[BaseModel] = GetEstimatesFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    def _run(
        self,
        identifiers: list[str],
        estimate_type: EstimateType,
        period_type: EstimatePeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
        num_periods_forward: int | None = None,
        num_periods_backward: int | None = None,
    ) -> GetEstimatesFromIdentifiersResp:
        """Sample response:

         meow meow meow meow meow
        """

        api_client = self.kfinance_client.kfinance_api_client
        ids_response = api_client.unified_fetch_id_triples(identifiers)
        company_id_to_identifier = {
            id_triple.company_id: identifier
            for identifier, id_triple in ids_response.identifiers_to_id_triples.items()
        }
        company_ids = [
            id_triple.company_id for id_triple in ids_response.identifiers_to_id_triples.values()
        ]
        identifier_to_results = {}
        all_errors = []
        for company_id in company_ids:
            response = api_client.fetch_estimates(
                company_id=company_id,
                estimate_type=estimate_type,
                period_type=period_type,
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
                num_periods_forward=num_periods_forward,
                num_periods_backward=num_periods_backward,
            )
            original_identifier = company_id_to_identifier[company_id]
            identifier_to_results[original_identifier] = response.results
            if response.errors:
                all_errors.append(response.errors)

        # maybe truncate the results if there's too much?

        return GetEstimatesFromIdentifiersResp(
            results=identifier_to_results, errors=all_errors
        )
