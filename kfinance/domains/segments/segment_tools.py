from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.models.date_and_period_models import NumPeriods, NumPeriodsBack, PeriodType
from kfinance.client.permission_models import Permission
from kfinance.domains.line_items.line_item_models import CalendarType
from kfinance.domains.segments.segment_models import SegmentsResp, SegmentType
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ValidQuarter,
)


class GetSegmentsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    segment_type: SegmentType
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: ValidQuarter | None = Field(default=None, description="Starting quarter")
    end_quarter: ValidQuarter | None = Field(default=None, description="Ending quarter")
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


class GetSegmentsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, SegmentsResp]  # identifier -> response


class GetSegmentsFromIdentifiers(KfinanceTool):
    name: str = "get_segments_from_identifiers"
    description: str = dedent("""
        Get the templated business or geographic segments associated with a list of identifiers.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - To fetch the most recent segment data, leave all time parameters as null.
        - To filter by time, use either absolute time (start_year, end_year, start_quarter, end_quarter) OR relative time (num_periods, num_periods_back)—but not both.
        - Set calendar_type based on how the query references the time period—use "fiscal" for fiscal year references and "calendar" for calendar year references.
        - When calendar_type=None, it defaults to 'fiscal'.
        - Exception: with multiple identifiers and absolute time, calendar_type=None defaults to 'calendar' for cross-company comparability; calendar_type='fiscal' returns fiscal data but should not be compared across companies since fiscal years have different end dates.

        Examples:
        Query: "What are the business segments for AT&T?"
        Function: get_segments_from_identifiers(identifiers=["AT&T"], segment_type="business")

        Query: "Get most recent geographic segments for Pfizer and JNJ"
        Function: get_segments_from_identifiers(identifiers=["Pfizer", "JNJ"], segment_type="geographic")

        Query: "What are the ltm business segments for SPGI for the last three calendar quarters but one?"
        Function: get_segments_from_identifiers(segment_type="business", period_type="ltm", calendar_type="calendar", num_periods=2, num_periods_back=1, identifiers=["SPGI"])
    """).strip()
    args_schema: Type[BaseModel] = GetSegmentsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.SegmentsPermission}

    def _run(
        self,
        identifiers: list[str],
        segment_type: SegmentType,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
        calendar_type: CalendarType | None = None,
        num_periods: int | None = None,
        num_periods_back: int | None = None,
    ) -> GetSegmentsFromIdentifiersResp:
        """Sample response:

        {
            'results': {
                'SPGI': {
                    'currency': 'USD',
                    'periods': {
                        'CY2021': {
                            'period_end_date': '2021-12-31',
                            'num_months': 12,
                            'segments': [
                                {
                                    'name': 'Commodity Insights',
                                    'line_items': [
                                        {
                                            'name': 'CAPEX',
                                            'value': -2000000.0,
                                            'sources': [
                                                {
                                                    'type': 'doc-viewer segment',
                                                    'url': 'https://www.capitaliq.spglobal.com/...'
                                                }
                                            ]
                                        },
                                        {
                                            'name': 'D&A',
                                            'value': 12000000.0
                                        }
                                    ]
                                },
                                {
                                    'name': 'Unallocated Assets Held for Sale',
                                    'line_items': [
                                        {
                                            'name': 'Total Assets',
                                            'value': 321000000.0
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """

        api_client = self.kfinance_client.kfinance_api_client

        # First resolve identifiers to company IDs
        ids_response = api_client.unified_fetch_id_triples(identifiers)

        # Call the simplified fetch_segments API with company IDs
        response = api_client.fetch_segments(
            company_ids=ids_response.company_ids,
            segment_type=segment_type,
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
        for company_id_str, segments_resp in response.results.items():
            company_id = int(company_id_str)
            original_identifier = ids_response.get_identifier_from_company_id(company_id)
            identifier_to_results[original_identifier] = segments_resp

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
            for segments_response in identifier_to_results.values():
                segments_response.remove_all_periods_other_than_the_most_recent_one()

        all_errors = list(ids_response.errors.values()) + list(response.errors.values())

        return GetSegmentsFromIdentifiersResp(results=identifier_to_results, errors=all_errors)
