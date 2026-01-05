from difflib import SequenceMatcher
from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field, model_validator

from kfinance.client.models.date_and_period_models import NumPeriods, NumPeriodsBack, PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import (
    LINE_ITEM_NAMES_AND_ALIASES,
    LINE_ITEM_TO_DESCRIPTIONS_MAP,
    CalendarType,
    LineItemResp,
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
    calendar_type: CalendarType | None = Field(
        default=None, description="Fiscal year or calendar year"
    )
    num_periods: NumPeriods | None = Field(
        default=None, description="The number of periods to retrieve data for (1-99)"
    )
    num_periods_back: NumPeriodsBack | None = Field(
        default=None,
        description="The end period of the data range expressed as number of periods back relative to the present period (0-99)",
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
    results: dict[str, LineItemResp]  # identifier -> response


class GetFinancialLineItemFromIdentifiers(KfinanceTool):
    name: str = "get_financial_line_item_from_identifiers"
    description: str = dedent("""
        Get the financial line item associated with a list of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent value, leave all time parameters as null.
        - Line item names are case-insensitive, use underscores, and support common aliases (e.g., 'revenue' and 'normal_revenue' return the same data).
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods, num_periods_back)—but not both.
        - Set calendar_type based on how the query references the time period—use "fiscal" for fiscal year references and "calendar" for calendar year references.
        - When calendar_type=None, it defaults to 'fiscal'.
        - Exception: with multiple identifiers and absolute time, calendar_type=None defaults to 'calendar' for cross-company comparability; calendar_type='fiscal' returns fiscal data but should not be compared across companies since fiscal years have different end dates.

        Examples:
        Query: "Get MSFT and AAPL revenue quarterly"
        Function: get_financial_line_item_from_identifiers(line_item="revenue", identifiers=["MSFT", "AAPL"], period_type="quarterly")

        Query: "General Electric's ebt excluding unusual items for FY2023"
        Function: get_financial_line_item_from_identifiers(line_item="ebt_excluding_unusual_items", identifiers=["General Electric"], period_type="annual", calendar_type="fiscal", start_year=2023, end_year=2023)

        Query: "What is the most recent three quarters except one ppe for Exxon and Hasbro?"
        Function: get_financial_line_item_from_identifiers(line_item="ppe", period_type="quarterly", num_periods=2, num_periods_back=1, identifiers=["Exxon", "Hasbro"])

        Query: "What are the ytd operating income values for Hilton for the calendar year 2022?"
        Function: get_financial_line_item_from_identifiers(line_item="operating_income", period_type="ytd", calendar_type="calendar", start_year=2022, end_year=2022, identifiers=["Hilton"])

        Query: "Compare AAPL and MSFT revenue for 2023"
        Function: get_financial_line_item_from_identifiers(line_item="revenue", identifiers=["AAPL", "MSFT"], period_type="annual", calendar_type="calendar", start_year=2023, end_year=2023)
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
        calendar_type: CalendarType | None = None,
        num_periods: int | None = None,
        num_periods_back: int | None = None,
    ) -> GetFinancialLineItemFromIdentifiersResp:
        """Sample response:

        {
            'SPGI': {
                'currency': 'USD',
                'periods': {
                    'FY2022': {
                        'period_end_date': '2022-12-31',
                        'num_months': 12,
                        'line_item': {
                            'name': 'Revenue',
                            'value': 11181000000.0,
                            'sources': [
                                {
                                    'type': 'doc-viewer line item',
                                    'url': 'https://www.capitaliq.spglobal.com/...'
                                }
                            ]
                        }
                    },
                    'FY2023': {
                        'period_end_date': '2023-12-31',
                        'num_months': 12,
                        'line_item': {
                            'name': 'Revenue',
                            'value': 12497000000.0,
                            'sources': [
                                {
                                    'type': 'doc-viewer line item',
                                    'url': 'https://www.capitaliq.spglobal.com/...'
                                }
                            ]
                        }
                    }
                }
            }
        }

        """
        api_client = self.kfinance_client.kfinance_api_client

        # First resolve identifiers to company IDs
        ids_response = api_client.unified_fetch_id_triples(identifiers)

        response = api_client.fetch_line_item(
            company_ids=ids_response.company_ids,
            line_item=line_item,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            calendar_type=calendar_type,
            num_periods=num_periods,
            num_periods_back=num_periods_back,
        )

        identifier_to_results = {}
        for company_id_str, line_item_resp in response.results.items():
            original_identifier = ids_response.get_identifier_from_company_id(int(company_id_str))
            identifier_to_results[original_identifier] = line_item_resp

        # If no date and multiple companies, only return the most recent value.
        # By default, we return 5 years of data, which can be too much when
        # returning data for many companies.
        if (
            start_year is None
            and end_year is None
            and start_quarter is None
            and end_quarter is None
            and num_periods is None
            and num_periods_back is None
            and len(identifier_to_results) > 1
        ):
            for line_item_response in identifier_to_results.values():
                line_item_response.remove_all_periods_other_than_the_most_recent_one()

        all_errors = list(ids_response.errors.values()) + list(response.errors.values())

        return GetFinancialLineItemFromIdentifiersResp(
            results=identifier_to_results, errors=all_errors
        )
