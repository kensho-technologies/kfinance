from datetime import datetime
from functools import cache, cached_property
import logging
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional

import numpy as np
import pandas as pd

from .constants import LINE_ITEMS, BusinessRelationshipType
from .fetch import KFinanceApiClient


if TYPE_CHECKING:
    from .kfinance import BusinessRelationships


logger = logging.getLogger(__name__)


class CompanyFunctionsMetaClass:
    kfinance_api_client: KFinanceApiClient

    @cached_property
    def company_id(self) -> Any:
        """Set and return the company id for the object"""
        raise NotImplementedError("child classes must implement company id property")

    def validate_inputs(
        self,
        period_type: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> None:
        """Test the time inputs for validity."""

        if period_type not in {"annual", "quarterly", "ytd", "ltm", None}:
            raise RuntimeError(f"Period type {period_type} is not valid.")

        if start_year and (start_year > datetime.now().year):
            raise ValueError("start_year is in the future")

        if end_year and not (1900 < end_year < 2100):
            raise ValueError("end_year is not in range")

        if start_quarter and not (1 <= start_quarter <= 4):
            raise ValueError("start_qtr is out of range 1 to 4")

        if end_quarter and not (1 <= end_quarter <= 4):
            raise ValueError("end_qtr is out of range 1 to 4")

    @cache
    def statement(
        self,
        statement_type: str,
        period_type: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get the company's financial statement"""
        try:
            self.validate_inputs(
                period_type=period_type,
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
        period_type: Optional[str] = None,
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
        period_type: Optional[str] = None,
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
        period_type: Optional[str] = None,
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
        period_type: Optional[str] = None,
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
        period_type: Optional[str] = None,
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

    @cache
    def line_item(
        self,
        line_item: str,
        period_type: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_quarter: Optional[int] = None,
        end_quarter: Optional[int] = None,
    ) -> pd.DataFrame:
        """Get a DataFrame of a financial line item according to the date ranges."""
        try:
            self.validate_inputs(
                period_type=period_type,
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )
        except ValueError:
            return pd.DataFrame()

        return (
            pd.DataFrame(
                self.kfinance_api_client.fetch_line_item(
                    company_id=self.company_id,
                    line_item=line_item,
                    period_type=period_type,
                    start_year=start_year,
                    end_year=end_year,
                    start_quarter=start_quarter,
                    end_quarter=end_quarter,
                )
            )
            .transpose()
            .apply(pd.to_numeric)
            .replace(np.nan, None)
            .set_index(pd.Index([line_item]))
        )

    def relationships(self, relationship_type: BusinessRelationshipType) -> "BusinessRelationships":
        """Returns a BusinessRelationships object that includes the current and previous Companies associated with company_id and filtered by relationship_type. The function calls fetch_companies_from_business_relationship.

        :param relationship_type: The type of relationship to filter by. Valid relationship types are defined in the BusinessRelationshipType class.
        :type relationship_type: BusinessRelationshipType
        :return: A BusinessRelationships object containing a tuple of Companies objects that lists current and previous company IDs that have the specified relationship with the given company_id.
        :rtype: BusinessRelationships
        """
        from .kfinance import BusinessRelationships, Companies

        companies = self.kfinance_api_client.fetch_companies_from_business_relationship(
            self.company_id,
            relationship_type,
        )
        return BusinessRelationships(
            Companies(self.kfinance_api_client, companies["current"]),
            Companies(self.kfinance_api_client, companies["previous"]),
        )

    def market_cap(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves market caps for a company between start and end date.

        :param start_date: The start date in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A DataFrame with a `market_cap` column. The dates are the index.
        :rtype: pd.DataFrame
        """

        return self._fetch_market_cap_tev_or_shares_outstanding(
            column_to_extract="market_cap", start_date=start_date, end_date=end_date
        )

    def tev(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves TEV (total enterprise value) for a company between start and end date.

        :param start_date: The start date in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A DataFrame with a `tev` column. The dates are the index.
        :rtype: pd.DataFrame
        """

        return self._fetch_market_cap_tev_or_shares_outstanding(
            column_to_extract="tev", start_date=start_date, end_date=end_date
        )

    def shares_outstanding(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieves shares outstanding for a company between start and end date.

        :param start_date: The start date in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A DataFrame with a `shares_outstanding` column. The dates are the index.
        :rtype: pd.DataFrame
        """

        return self._fetch_market_cap_tev_or_shares_outstanding(
            column_to_extract="shares_outstanding", start_date=start_date, end_date=end_date
        )

    def _fetch_market_cap_tev_or_shares_outstanding(
        self,
        column_to_extract: Literal["market_cap", "tev", "shares_outstanding"],
        start_date: str | None,
        end_date: str | None,
    ) -> pd.DataFrame:
        """Helper function to fetch market cap, TEV, and shares outstanding."""

        df = pd.DataFrame(
            self.kfinance_api_client.fetch_market_caps_tevs_and_shares_outstanding(
                company_id=self.company_id, start_date=start_date, end_date=end_date
            )["market_caps"]
        )
        return df.set_index("date")[[column_to_extract]].apply(pd.to_numeric).replace(np.nan, None)


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

    @cached_property
    def company(self) -> Any:
        """Set and return the company for the object"""
        raise NotImplementedError("child classes must implement company property")


for relationship in BusinessRelationshipType:

    def _relationship_outer_wrapper(relationship_type: BusinessRelationshipType) -> cached_property:
        """Creates a cached property for a relationship type.

        This function returns a property that retrieves the associated company's current and previous
        relationships of the specified type.

        Args:
            relationship_type (BusinessRelationshipType): The type of relationship to be wrapped.

        Returns:
            property: A cached property that calls the inner wrapper to retrieve the relationship data.
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

        return cached_property(relationship_inner_wrapper)

    relationship_cached_property = _relationship_outer_wrapper(relationship)
    relationship_cached_property.__set_name__(CompanyFunctionsMetaClass, relationship)
    setattr(
        CompanyFunctionsMetaClass,
        relationship,
        relationship_cached_property,
    )
