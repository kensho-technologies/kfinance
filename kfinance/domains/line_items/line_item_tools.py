from difflib import SequenceMatcher
from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field, model_validator

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.models.date_and_period_models import PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import (
    LINE_ITEM_NAMES_AND_ALIASES,
    LINE_ITEM_TO_DESCRIPTIONS_MAP,
    LineItemResponse,
    LineItemScore,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)


def _find_similar_line_items(
    invalid_item: str, descriptors: dict[str, str], max_suggestions: int = 8
) -> list[LineItemScore]:
    """Find similar line items using keyword matching and string similarity.

    Args:
        invalid_item: The invalid line item provided by the user
        descriptors: Dictionary mapping line item names to descriptions
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of LineItemScore objects for the best matches
    """
    if not descriptors:
        return []

    invalid_lower = invalid_item.lower()
    scores: list[LineItemScore] = []

    for line_item, description in descriptors.items():
        # Calculate similarity scores
        name_similarity = SequenceMatcher(None, invalid_lower, line_item.lower()).ratio()

        # Check for keyword matches in the line item name
        invalid_words = set(invalid_lower.replace("_", " ").split())
        item_words = set(line_item.lower().replace("_", " ").split())
        keyword_match_score = len(invalid_words.intersection(item_words)) / max(
            len(invalid_words), 1
        )

        # Check for keyword matches in description
        description_words = set(description.lower().split())
        description_match_score = len(invalid_words.intersection(description_words)) / max(
            len(invalid_words), 1
        )

        # Combined score (weighted)
        total_score = (
            name_similarity * 0.5  # Direct name similarity
            + keyword_match_score * 0.3  # Keyword matches in name
            + description_match_score * 0.2  # Keyword matches in description
        )

        scores.append(LineItemScore(name=line_item, description=description, score=total_score))

    # Sort by score (descending) and return top matches
    scores.sort(reverse=True, key=lambda x: x.score)
    return [item for item in scores[:max_suggestions] if item.score > 0.1]


def _smart_line_item_validator(v: str) -> str:
    """Custom validator that provides intelligent suggestions for invalid line items."""
    if v not in LINE_ITEM_NAMES_AND_ALIASES:
        # Find similar items using pre-computed descriptors
        suggestions = _find_similar_line_items(v, LINE_ITEM_TO_DESCRIPTIONS_MAP)

        if suggestions:
            suggestion_text = "\n\nDid you mean one of these?\n"
            for item in suggestions:
                suggestion_text += f"  • '{item.name}': {item.description}\n"

            error_msg = f"Invalid line_item '{v}'.{suggestion_text}"
        else:
            error_msg = f"Invalid line_item '{v}'. Please refer to the tool documentation for valid options."

        raise ValueError(error_msg)
    return v


class GetFinancialLineItemFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # Note: mypy will not enforce this literal because of the type: ignore.
    # But pydantic still uses the literal to check for allowed values and only includes
    # allowed values in generated schemas.
    line_item: Literal[tuple(LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of financial line_item requested"
    )
    period_type: PeriodType | None = Field(
        default=None, description="The period type (annual or quarterly)"
    )
    start_year: int | None = Field(
        default=None,
        description="The starting year for the data range. Use null for the most recent data.",
    )
    end_year: int | None = Field(
        default=None,
        description="The ending year for the data range. Use null for the most recent data.",
    )
    start_quarter: ValidQuarter | None = Field(
        default=None, description="Starting quarter (1-4). Only used when period_type is quarterly."
    )
    end_quarter: ValidQuarter | None = Field(
        default=None, description="Ending quarter (1-4). Only used when period_type is quarterly."
    )

    @model_validator(mode="before")
    @classmethod
    def validate_line_item_with_suggestions(cls, values: dict) -> dict:
        """Custom validator that provides intelligent suggestions for invalid line items."""
        if isinstance(values, dict) and "line_item" in values:
            line_item = values["line_item"]
            # Use the helper function to validate and provide suggestions
            _smart_line_item_validator(line_item)
        return values


class GetFinancialLineItemFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, LineItemResponse]


class GetFinancialLineItemFromIdentifiers(KfinanceTool):
    name: str = "get_financial_line_item_from_identifiers"
    description: str = dedent("""
        Get the financial line item associated with a list of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent value, leave start_year, start_quarter, end_year, and end_quarter as null.
        - The tool accepts arguments in calendar years, and all outputs will be in calendar years (may not align with fiscal year).
        - All aliases for a line item return identical data (e.g., 'revenue', 'normal_revenue', and 'regular_revenue' return the same data).
        - Line item names are case-insensitive and use underscores (e.g., 'total_revenue' not 'Total Revenue').

        Examples:
        Query: "What are the revenues of Lowe's and Home Depot?"
        Function: get_financial_line_item_from_identifiers(line_item="revenue", identifiers=["Lowe's", "Home Depot"])

        Query: "Get MSFT and AAPL revenue"
        Function: get_financial_line_item_from_identifiers(line_item="revenue", identifiers=["MSFT", "AAPL"])

        Query: "General Eletrics's ebt excluding unusual items for 2023"
        Function: get_financial_line_item_from_identifiers(line_item="ebt_excluding_unusual_items", identifiers=["General Eletric"], period_type="annual", start_year=2023, end_year=2023)
    """).strip()
    args_schema: Type[BaseModel] = GetFinancialLineItemFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {
        Permission.StatementsPermission,
        Permission.PrivateCompanyFinancialsPermission,
    }

    def _run(
        self,
        identifiers: list[str],
        line_item: str,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> GetFinancialLineItemFromIdentifiersResp:
        """Sample response:

        {
            'SPGI': {
                '2022': {'revenue': 11181000000.0},
                '2023': {'revenue': 12497000000.0},
                '2024': {'revenue': 14208000000.0}
            }
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_line_item,
                kwargs=dict(
                    company_id=id_triple.company_id,
                    line_item=line_item,
                    period_type=period_type,
                    start_year=start_year,
                    end_year=end_year,
                    start_quarter=start_quarter,
                    end_quarter=end_quarter,
                ),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        line_item_responses: dict[str, LineItemResponse] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )

        # If no date and multiple companies, only return the most recent value.
        # By default, we return 5 years of data, which can be too much when
        # returning data for many companies.
        if (
            start_year is None
            and end_year is None
            and start_quarter is None
            and end_quarter is None
            and len(line_item_responses) > 1
        ):
            for line_item_response in line_item_responses.values():
                if line_item_response.line_item:
                    most_recent_year = max(line_item_response.line_item.keys())
                    most_recent_year_data = line_item_response.line_item[most_recent_year]
                    line_item_response.line_item = {most_recent_year: most_recent_year_data}

        return GetFinancialLineItemFromIdentifiersResp(
            results=line_item_responses, errors=list(id_triple_resp.errors.values())
        )
