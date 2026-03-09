from abc import ABC, abstractmethod
from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import (
    EstimatePeriodType,
    EstimateType,
    NumPeriodsBackward,
    NumPeriodsForward,
)
from kfinance.client.permission_models import Permission
from kfinance.domains.estimates.estimates_models import (
    AnalystRecommendationsResp,
    ConsensusTargetPriceResp,
    EstimatesResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)


class GetEstimatesFromIdentifiersArgs(ToolArgsWithIdentifiers):
    period_type: EstimatePeriodType | None = Field(
        default=None, description="The period type (annual, semi-annual, or quarterly)."
    )
    fiscal_start_year: int | None = Field(
        default=None,
        description="The starting year for the data range. Use null for the most recent data.",
    )
    fiscal_end_year: int | None = Field(
        default=None,
        description="The ending year for the data range. Use null for the most recent data.",
    )
    fiscal_start_quarter: ValidQuarter | None = Field(
        default=None,
        description="Starting quarter (1-4). Used when period_type is semi-annual or quarterly.",
    )
    fiscal_end_quarter: ValidQuarter | None = Field(
        default=None,
        description="Ending quarter (1-4). Used when period_type is semi-annual or quarterly.",
    )
    num_periods_forward: NumPeriodsForward | None = Field(
        default=None, description="The number of periods forward from today (1-99)."
    )
    num_periods_backward: NumPeriodsBackward | None = Field(
        default=None,
        description="The number of periods to look back from today (1-99).",
    )


class GetEstimatesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, EstimatesResp]  # identifier -> response


class GetEstimatesFromIdentifiers(KfinanceTool, ABC):
    args_schema: Type[BaseModel] = GetEstimatesFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    @property
    @abstractmethod
    def estimate_type(self) -> EstimateType:
        """The estimate type property."""
        pass

    def _run(
        self,
        identifiers: list[str],
        period_type: EstimatePeriodType | None = None,
        fiscal_start_year: int | None = None,
        fiscal_end_year: int | None = None,
        fiscal_start_quarter: Literal[1, 2, 3, 4] | None = None,
        fiscal_end_quarter: Literal[1, 2, 3, 4] | None = None,
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
                start_year=fiscal_start_year,
                end_year=fiscal_end_year,
                start_quarter=fiscal_start_quarter,
                end_quarter=fiscal_end_quarter,
                num_periods_forward=num_periods_forward,
                num_periods_backward=num_periods_backward,
            )
            original_identifier = company_id_to_identifier[company_id]
            identifiers_to_results[original_identifier] = response.results[str(company_id)]
            if response.errors and "errors" in response.errors:
                all_errors.append(response.errors["errors"])

        all_errors = list(ids_response.errors.values()) + all_errors

        return GetEstimatesFromIdentifiersResp(results=identifiers_to_results, errors=all_errors)


class GetConsensusEstimatesFromIdentifiers(GetEstimatesFromIdentifiers):
    name: str = "get_consensus_estimates_from_identifiers"
    description: str = dedent("""
        Get consensus analyst estimates (EPS, Revenue, EBITDA, etc.) for a given company id. Returns statistical aggregates including high, low, mean, median, and number of estimates. When periods have ended, actual reported values are also returned.
    """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        """The estimate type is consensus."""
        return EstimateType.consensus


class GetGuidanceFromIdentifiers(GetEstimatesFromIdentifiers):
    name: str = "get_guidance_from_identifiers"
    description: str = dedent("""
        Get company-issued financial guidance for a given company id. Returns the most recent guidance provided by the company for future periods, or the final guidance issued before results were reported for past periods.
    """).strip()

    @property
    def estimate_type(self) -> EstimateType:
        """The estimate type is guidance."""
        return EstimateType.guidance


class GetConsensusTargetPriceFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, ConsensusTargetPriceResp]


class GetConsensusTargetPriceFromIdentifiers(KfinanceTool):
    name: str = "get_consensus_target_price_from_identifiers"
    description: str = dedent("""
        Get consensus target price estimates for a given company. Returns the current consensus analyst target price including high, low, mean, and median values.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    def _run(
        self,
        identifiers: list[str],
    ) -> GetConsensusTargetPriceFromIdentifiersResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        company_id_to_identifier = {
            id_triple.company_id: identifier
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        }
        identifiers_to_results = {}
        all_errors: list[str] = []
        for company_id, identifier in company_id_to_identifier.items():
            response = api_client.fetch_consensus_target_price(company_id=company_id)
            identifiers_to_results[identifier] = response.results[str(company_id)]
            if response.errors and "errors" in response.errors:
                all_errors.append(response.errors["errors"])

        all_errors = list(id_triple_resp.errors.values()) + all_errors

        return GetConsensusTargetPriceFromIdentifiersResp(
            results=identifiers_to_results, errors=all_errors
        )


class GetAnalystRecommendationsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, AnalystRecommendationsResp]


class GetAnalystRecommendationsFromIdentifiers(KfinanceTool):
    name: str = "get_analyst_recommendations_from_identifiers"
    description: str = dedent("""
        Get analyst recommendations for a given company. Returns the current consensus analyst recommendation breakdown including buy, hold, sell counts and overall rating.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.EstimatesPermission}

    def _run(
        self,
        identifiers: list[str],
    ) -> GetAnalystRecommendationsFromIdentifiersResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        company_id_to_identifier = {
            id_triple.company_id: identifier
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        }
        identifiers_to_results = {}
        all_errors: list[str] = []
        for company_id, identifier in company_id_to_identifier.items():
            response = api_client.fetch_analyst_recommendations(company_id=company_id)
            identifiers_to_results[identifier] = response.results[str(company_id)]
            if response.errors and "errors" in response.errors:
                all_errors.append(response.errors["errors"])

        all_errors = list(id_triple_resp.errors.values()) + all_errors

        return GetAnalystRecommendationsFromIdentifiersResp(
            results=identifiers_to_results, errors=all_errors
        )
