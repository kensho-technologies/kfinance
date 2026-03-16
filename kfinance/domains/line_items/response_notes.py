from typing import Protocol

from kfinance.client.models.date_and_period_models import EstimatePeriodType, PeriodType
from kfinance.domains.line_items.line_item_models import CalendarType


class ResponseModelWithNotesField(Protocol):
    notes: list[str]


SOURCE_LINK_NOTE = (
    "When displaying `line_item` values that include a doc-viewer `url` in their `sources` "
    "attribute, turn the values into clickable links. Format as markdown links: "
    "[$123.4B](source_url). Do not add separate 'Source' labels."
)

FISCAL_PERIOD_WARNING = (
    "Warning: Fiscal periods may differ between companies. "
    "Before comparing data, verify that period end dates align. "
    "If misaligned, clearly state that the comparison is approximate."
)

FISCAL_YEAR_TERMINOLOGY_WARNING = (
    "When reporting data in fiscal years, always refer to it as 'Fiscal Year' or 'FY', "
    "never as 'Calendar Year'. This applies even when the fiscal year ends on December 31st. "
    "Only use 'Calendar Year' (CY) when the data was explicitly requested and returned in "
    "calendar year format."
)


def insert_source_link_note(resp_model: ResponseModelWithNotesField) -> None:
    """Add a note about how to use sources into a tool response."""
    resp_model.notes.append(SOURCE_LINK_NOTE)


def insert_fiscal_period_notes(
    calendar_type: CalendarType | None,
    period_type: PeriodType | EstimatePeriodType | None,
    resp_model: ResponseModelWithNotesField,
) -> None:
    """Add notes about fiscal periods where necessary into a tool response."""
    if calendar_type is CalendarType.fiscal or calendar_type is None:
        resp_model.notes.append(FISCAL_PERIOD_WARNING)
        # Check if period_type is annual
        if (
            period_type is None
            or period_type is PeriodType.annual
            or period_type is EstimatePeriodType.annual
        ):
            resp_model.notes.append(FISCAL_YEAR_TERMINOLOGY_WARNING)
