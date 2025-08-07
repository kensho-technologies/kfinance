from abc import abstractmethod
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

from cachetools import LRUCache, cached
import numpy as np
import pandas as pd

from kfinance.client.fetch import KFinanceApiClient
from kfinance.client.models.date_and_period_models import PeriodType
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
)
from kfinance.domains.capitalizations.capitalization_models import Capitalization
from kfinance.domains.competitors.competitor_models import CompetitorSource
from kfinance.domains.line_items.line_item_models import LINE_ITEMS
from kfinance.domains.segments.segment_models import SegmentType


if TYPE_CHECKING:
    from .kfinance import BusinessRelationships, Companies

logger = logging.getLogger(__name__)


class CompanyFunctionsMetaClass:
    kfinance_api_client: KFinanceApiClient

    @property
    @abstractmethod
    def company_id(self) -> Any:
        """Set and return the company id for the object"""
        raise NotImplementedError("child classes must implement company id property")

    def validate_inputs(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> None:
        """Test the time inputs for validity."""

        if start_year and (start_year > datetime.now().year):
            raise ValueError("start_year is in the future")

        if end_year and not (1900 < end_year < 2100):
            raise ValueError("end_year is not in range")

        if start_quarter and not (1 <= start_quarter <= 4):
            raise ValueError("start_qtr is out of range 1 to 4")

        if end_quarter and not (1 <= end_quarter <= 4):
            raise ValueError("end_qtr is out of range 1 to 4")

    @cached(cache=LRUCache(maxsize=100))
    def statement(
        self,
        statement_type: str,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get the company's financial statement"""
        try:
            self.validate_inputs(
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )
        except ValueError:
            return pd.DataFrame()

        return (
            pd.DataFrame(
                self.kfinance_api_client.fetch_statement(
                    company_id=self.company_id,
                    statement_type=statement_type,
                    period_type=period_type,
                    start_year=start_year,
                    end_year=end_year,
                    start_quarter=start_quarter,
                    end_quarter=end_quarter,
                )["statements"]
            )
            .apply(pd.to_numeric)
            .replace(np.nan, None)
        )

    def income_statement(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """The templated income statement"""
        return self.statement(
            statement_type="income_statement",
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    def income_stmt(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """The templated income statement"""
        return self.statement(
            statement_type="income_statement",
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    def balance_sheet(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """The templated balance sheet"""
        return self.statement(
            statement_type="balance_sheet",
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    def cash_flow(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """The templated cash flow statement"""
        return self.statement(
            statement_type="cash_flow",
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    def cashflow(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """The templated cash flow statement"""
        return self.statement(
            statement_type="cash_flow",
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    @cached(cache=LRUCache(maxsize=100))
    def line_item(
        self,
        line_item: str,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get a DataFrame of a financial line item according to the date ranges."""
        try:
            self.validate_inputs(
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )
        except ValueError:
            return pd.DataFrame()

        line_item_response = self.kfinance_api_client.fetch_line_item(
            company_id=self.company_id,
            line_item=line_item,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )
        return (
            pd.DataFrame({"line_item": line_item_response.line_item})
            .transpose()
            .apply(pd.to_numeric)
            .replace(np.nan, None)
            .set_index(pd.Index([line_item]))
        )

    @cached(cache=LRUCache(maxsize=100))
    def relationships(self, relationship_type: BusinessRelationshipType) -> "BusinessRelationships":
        """Returns a BusinessRelationships object that includes the current and previous Companies associated with company_id and filtered by relationship_type. The function calls fetch_companies_from_business_relationship.

        :param relationship_type: The type of relationship to filter by. Valid relationship types are defined in the BusinessRelationshipType class.
        :type relationship_type: BusinessRelationshipType
        :return: A BusinessRelationships object containing a tuple of Companies objects that lists current and previous company IDs that have the specified relationship with the given company_id.
        :rtype: BusinessRelationships
        """
        from .kfinance import BusinessRelationships, Companies

        relationship_resp = self.kfinance_api_client.fetch_companies_from_business_relationship(
            company_id=self.company_id,
            relationship_type=relationship_type,
        )
        return BusinessRelationships(
            current=Companies(
                kfinance_api_client=self.kfinance_api_client,
                company_ids=[c.company_id for c in relationship_resp.current],
            ),
            previous=Companies(
                kfinance_api_client=self.kfinance_api_client,
                company_ids=[c.company_id for c in relationship_resp.previous],
            ),
        )

    def market_cap(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Retrieves market caps for a company between start and end date.

        :param start_date: The start date in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A dict with market_cap
        :rtype: dict
        """

        return self._fetch_market_cap_tev_or_shares_outstanding(
            capitalization_to_extract=Capitalization.market_cap,
            start_date=start_date,
            end_date=end_date,
        )

    def tev(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Retrieves TEV (total enterprise value) for a company between start and end date.

        :param start_date: The start date in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A dict with TEV
        :rtype: dict
        """

        return self._fetch_market_cap_tev_or_shares_outstanding(
            capitalization_to_extract=Capitalization.tev, start_date=start_date, end_date=end_date
        )

    def shares_outstanding(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Retrieves shares outstanding for a company between start and end date.

        :param start_date: The start date in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A dict with outstanding shares
        :rtype: dict
        """

        return self._fetch_market_cap_tev_or_shares_outstanding(
            capitalization_to_extract=Capitalization.shares_outstanding,
            start_date=start_date,
            end_date=end_date,
        )

    def _fetch_market_cap_tev_or_shares_outstanding(
        self,
        capitalization_to_extract: Capitalization,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        """Helper function to fetch market cap, TEV, and shares outstanding."""

        capitalizations = self.kfinance_api_client.fetch_market_caps_tevs_and_shares_outstanding(
            company_id=self.company_id, start_date=start_date, end_date=end_date
        )
        return capitalizations.model_dump_json_single_metric(
            capitalization_metric=capitalization_to_extract
        )

    def _segments(
        self,
        segment_type: SegmentType,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> dict:
        """Get the company's segments"""
        try:
            self.validate_inputs(
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )
        except ValueError:
            return {}

        return self.kfinance_api_client.fetch_segments(
            company_id=self.company_id,
            segment_type=segment_type,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )["segments"]

    def business_segments(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> dict:
        """Retrieves the templated line of business segments for a given period_type, start_year, start_quarter, end_year and end_quarter.

        :param period_type: The period_type requested for. Can be “annual”, “quarterly”, "ytd". Defaults to “annual” when start_quarter and end_quarter are None.
        :type start_year: PeriodType, optional
        :param start_year: The starting calendar year, defaults to None
        :type start_year: int, optional
        :param end_year: The ending calendar year, defaults to None
        :type end_year: int, optional
        :param start_quarter: The starting calendar quarter, defaults to None
        :type start_quarter: int, optional
        :param end_quarter: The ending calendar quarter, defaults to None
        :type end_quarter: int, optional
        :return: A dictionary containing the templated line of business segments for each time period, segment name, line item, and value.
        :rtype: dict
        """
        return self._segments(
            segment_type=SegmentType.business,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    def geographic_segments(
        self,
        period_type: Optional[PeriodType] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> dict:
        """Retrieves the templated geographic segments for a given period_type, start_year, start_quarter, end_year and end_quarter.

        :param period_type: The period_type requested for. Can be “annual”, “quarterly”, "ytd". Defaults to “annual” when start_quarter and end_quarter are None.
        :type start_year: PeriodType, optional
        :param start_year: The starting calendar year, defaults to None
        :type start_year: int, optional
        :param end_year: The ending calendar year, defaults to None
        :type end_year: int, optional
        :param start_quarter: The starting calendar quarter, defaults to None
        :type start_quarter: int, optional
        :param end_quarter: The ending calendar quarter, defaults to None
        :type end_quarter: int, optional
        :return: A dictionary containing the templated geographic segments for each time period, segment name, line item, and value.
        :rtype: dict
        """
        return self._segments(
            segment_type=SegmentType.geographic,
            period_type=period_type,
            start_year=start_year,
            end_year=end_year,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
        )

    def competitors(
        self, competitor_source: CompetitorSource = CompetitorSource.all
    ) -> "Companies":
        """Get the list of company_id and company_name that are competitors of company_id, optionally filtered by the competitor_source type.

        :return: The list of company_id and company_name that are competitors of company_id, optionally filtered by the competitor_source type
        :rtype: Companies
        """
        from .kfinance import Companies, Company

        competitors_data = self.kfinance_api_client.fetch_competitors(
            company_id=self.company_id, competitor_source=competitor_source
        )
        return Companies(
            kfinance_api_client=self.kfinance_api_client,
            companies=[
                Company(
                    kfinance_api_client=self.kfinance_api_client,
                    company_id=company.company_id,
                    company_name=company.company_name,
                )
                for company in competitors_data.competitors
            ],
        )


for line_item in LINE_ITEMS:
    line_item_name = line_item["name"]

    def _line_item_outer_wrapper(line_item_name: str, alias_for: Optional[str] = None) -> Callable:
        def line_item_inner_wrapper(
            self: Any,
            period_type: Optional[str] = None,
            start_year: Optional[int] = None,
            end_year: Optional[int] = None,
            start_quarter: Optional[int] = None,
            end_quarter: Optional[int] = None,
        ) -> pd.DataFrame:
            return self.line_item(
                line_item=line_item_name,
                period_type=period_type,
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )

        doc = "ciq data item " + str(line_item["dataitemid"])
        TAB = "    "
        if alias_for is not None:
            doc = f"alias for {alias_for}\n\n{TAB}{TAB}" + doc
        line_item_inner_wrapper.__doc__ = doc
        line_item_inner_wrapper.__name__ = line_item_name
        return line_item_inner_wrapper

    setattr(
        CompanyFunctionsMetaClass,
        line_item_name,
        _line_item_outer_wrapper(line_item_name),
    )

    for alias in line_item["aliases"]:
        setattr(
            CompanyFunctionsMetaClass,
            alias,
            _line_item_outer_wrapper(alias, line_item_name),
        )


class DelegatedCompanyFunctionsMetaClass(CompanyFunctionsMetaClass):
    """all methods in CompanyFunctionsMetaClass delegated to company attribute"""

    def __init__(self) -> None:
        """delegate CompanyFunctionsMetaClass methods to company attribute"""
        super().__init__()
        company_function_names = [
            company_function
            for company_function in dir(CompanyFunctionsMetaClass)
            if not company_function.startswith("__")
            and callable(getattr(CompanyFunctionsMetaClass, company_function))
        ]
        for company_function_name in company_function_names:

            def delegated_function(company_function_name: str) -> Callable:
                # wrapper is necessary so that self.company is lazy loaded
                def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                    fn = getattr(self.company, company_function_name)
                    response = fn(*args, **kwargs)
                    return response

                company_function = getattr(
                    DelegatedCompanyFunctionsMetaClass, company_function_name
                )
                wrapper.__doc__ = company_function.__doc__
                wrapper.__name__ = company_function.__name__
                return wrapper

            setattr(
                DelegatedCompanyFunctionsMetaClass,
                company_function_name,
                delegated_function(company_function_name),
            )

    @property
    def company(self) -> Any:
        """Set and return the company for the object"""
        raise NotImplementedError("child classes must implement company property")


for relationship in BusinessRelationshipType:

    def _relationship_outer_wrapper(relationship_type: BusinessRelationshipType) -> property:
        """Creates a property for a relationship type.

        This function returns a property that retrieves the associated company's current and previous
        relationships of the specified type.

        Args:
            relationship_type (BusinessRelationshipType): The type of relationship to be wrapped.

        Returns:
            property: A property that calls the inner wrapper to retrieve the relationship data.
        """

        def relationship_inner_wrapper(
            self: Any,
        ) -> "BusinessRelationships":
            """Inner wrapper function for the relationship type.

            This function retrieves the associated company's current and previous relationships
            of the specified type.

            Returns:
                BusinessRelationships: A BusinessRelationships object containing the current and previous companies
                associated with the relationship type.
            """
            return self.relationships(relationship_type)

        doc = f"Returns the associated company's current and previous {relationship_type}s"
        relationship_inner_wrapper.__doc__ = doc
        relationship_inner_wrapper.__name__ = relationship

        return property(relationship_inner_wrapper)

    relationship_property = _relationship_outer_wrapper(relationship)
    setattr(
        CompanyFunctionsMetaClass,
        relationship,
        relationship_property,
    )
