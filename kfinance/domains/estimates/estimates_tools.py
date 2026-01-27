from abc import ABC, abstractmethod
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

class GetEstimatesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    period_type: EstimatePeriodType | None = Field(default=None, description="The period type (annual, semi-annual, or quarterly")
    start_year: int | None = Field(default=None, description="The starting year for the data range. Use null for the most recent data.")
    end_year: int | None = Field(default=None, description="The ending year for the data range. Use null for the most recent data.")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter (1-4). Used when period_type is semi-annual or quarterly.")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter (1-4). Used when period_type is semi-annual or quarterly.")
    num_periods_forward: NumPeriodsForward | None = Field(
        default=None, description="The number of periods forward from today (1-99)."
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None, description="The number of periods to look back from today (1-99).",
    )


class GetEstimatesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EstimatesResp]  # identifier -> response

class GetEstimatesFromIdentifiers(KfinanceTool, ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    args_schema: Type[BaseModel] = GetEstimatesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    @property
    @abstractmethod
    def estimate_type(self) -> EstimateType:
        pass

    def _run(
        self,
        identifiers: list[str],
        period_type: EstimatePeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
        num_periods_forward: int | None = None,
        num_periods_backward: int | None = None,
    ) -> GetEstimatesFromIdentifiersResp:
        """Sample response:

            "SPGI": {
                "estimate_type": "consensus",
                "currency": "USD",
                "period_type": "quarterly",
                "periods": {
                    "FY2025Q4": {
                        "period_end_date": "2025-12-31",
                        "estimates": [
                            {
                                "name": "Revenue Consensus High",
                                "value": "3955000000.000000",
                            },
                            {
                                "name": "Revenue Consensus Low",
                                "value": "3806400000.000000",
                            },
                            {
                                "name": "Revenue Consensus Mean",
                                "value": "3881725460.000000",
                            },
                            {
                                "name": "Revenue Consensus Median",
                                "value": "3883000000.000000",
                            },
                        ],
                    }
                },
            }
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
        identifiers_to_results = {}
        all_errors = []
        for company_id in company_ids:
            response = api_client.fetch_estimates(
                company_id=company_id,
                estimate_type=self.estimate_type,
                period_type=period_type,
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
                num_periods_forward=num_periods_forward,
                num_periods_backward=num_periods_backward,
            )
            original_identifier = company_id_to_identifier[company_id]
            identifiers_to_results[original_identifier] = response.results
            if response.errors:
                all_errors.append(response.errors)

        # If no date and multiple companies, only return the most recent value.
        # By default, we return 5 years of data, which can be too much when
        # returning data for many companies.
        if (
            start_year is None
            and end_year is None
            and start_quarter is None
            and end_quarter is None
            and num_periods_forward is None
            and num_periods_backward is None
            and len(identifiers_to_results) > 1
        ):
            for line_item_response in identifiers_to_results.values():
                if line_item_response.periods:
                    most_recent_year = max(line_item_response.periods.keys())
                    most_recent_year_data = line_item_response.periods[most_recent_year]
                    line_item_response.periods = {most_recent_year: most_recent_year_data}

        return GetEstimatesFromIdentifiersResp(
            results=identifiers_to_results, errors=all_errors
        )


class GetConsensusEstimatesFromIdentifiers(GetEstimatesFromIdentifiers):

    @property
    def name(self) -> str:
        return "get_consensus_estimates_from_identifiers"

    @property
    def description(self) -> str:
        return dedent("""
            Get consensus analyst estimates (EPS, Revenue, EBITDA, etc.) for a given company id. Returns statistical aggregates including high, low, mean, median, and number of estimates. When periods have ended, actual reported values are also returned.

            meow meow meow meow meow
        """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        return EstimateType.consensus


class GetGuidanceFromIdentifiers(GetEstimatesFromIdentifiers):

    @property
    def name(self) -> str:
        return "get_guidance_from_identifiers"

    @property
    def description(self) -> str:
        return dedent("""
            Get company-issued financial guidance for a given company id. Returns the most recent guidance provided by the company for future periods, or the final guidance issued before results were reported for past periods.

            meow meow meow meow meow
        """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        return EstimateType.guidance
