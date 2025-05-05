from datetime import date
import json
from textwrap import dedent
from typing import Literal, Optional, Sequence, Type

from constants import BusinessRelationshipType, Capitalization, PeriodType
import pandas as pd
from pydantic import BaseModel, Field
from tool_calling import KfinanceTool
from tool_calling.shared_models import CompanyDict

from kfinance.constants import LINE_ITEM_NAMES_AND_ALIASES
from kfinance.kfinance import BusinessRelationships


class ToolArgsWithTickerOrCompanyId(BaseModel):
    """Tool argument with a ticker or company_id."""

    ticker: str | None = Field(description="The ticker of a company", default=None)
    company_id: str | None = Field(description="The company_id of a company", default=None)


class ResolveCompaniesArgs(BaseModel):
    identifiers: list[str] | None = Field(description="A list of tickers, CUSIPs, or ISINs", default=None)

class ResolveCompanies(KfinanceTool):
    name: str = "resolve_companies"
    description: str = dedent("""
        Resolve a list of identifiers (tickers, CUSIPs, or ISINs) to a list of company dicts.

        Returns a list of dicts with keys "name", "company_id", "security_id", and "trading_item_id".
        """).strip()
    args_schema: Type[BaseModel] = ResolveCompaniesArgs

    def _run(self, tickers: list[str]) -> list[CompanyDict]:
        tickers_objects = [self.kfinance_client.ticker(ticker) for ticker in tickers]
        return [t.company_dict for t in tickers_objects]


class FilterCompaniesArgs(BaseModel):
    # no description because the description for enum fields comes from the enum docstring.
    country_iso_code: str | None = Field(
        description="The ISO 3166-1 Alpha-2 or Alpha-3 code that represent the primary country where the company is based.",
        default=None
    )
    state_iso_code: str | None = Field(
        description="The ISO 3166-2 Alpha-2 code that represents the primary subdivision of the country the firm the based in.",
        default=None
    )
    gics_industry: int | None = Field(
        description="The GICS industry to filter on. Use the numeric code, not the industry name. For example, for 'Oil & Gas Drilling' , pass 10101010.",
        default=None
    )
    exchange_code: str | None = Field(
        description="The exchange on which the company is listed.",
        default=None
    )


class FilterCompanies(KfinanceTool):
    name: str = "filter_companies"
    description: str = dedent("""
        Return the companies that match all of the defined filters.

        One of country_iso_code, gics_industry, or exchange_code must be supplied.
        """).strip()
    args_schema: Type[BaseModel] = FilterCompaniesArgs

    def _run(self,
             country_iso_code: Optional[str] = None,
             state_iso_code: Optional[str] = None,
             gics_industry: Optional[int] = None,
             exchange_code: Optional[str] = None
             ) -> list[str]:

        tickers = self.kfinance_client.tickers(
            country_iso_code=country_iso_code,
            state_iso_code=state_iso_code,
            exchange_code=exchange_code,
            gics=gics_industry
        )

        return [
            str(dict(name=ticker.name, company_id=ticker.company_id)) for ticker in tickers
        ][:100]



class GetCapitalizationFromIdentifierArgs(BaseModel):
    # no description because the description for enum fields comes from the enum docstring.
    capitalization: Capitalization
    company_ids: list[int] | None = Field(
        description="The company_ids for which the capitalization should be retrieved.",
        default=None
    )
    tickers: list[str] | None = Field(
        description="The tickers for which the capitalization should be retrieved.",
        default=None
    )
    start_date: date | None = Field(
        description="The start date for historical capitalization retrieval", default=None
    )
    end_date: date | None = Field(
        description="The end date for historical capitalization retrieval", default=None
    )


class GetCapitalization(KfinanceTool):
    name: str = "get_capitalization"
    description: str = dedent("""
        Get the historical market cap, tev (Total Enterprise Value), or shares outstanding for a group of company_ids between inclusive start_date and inclusive end date.

        - When possible, pass multiple company_ids in a single call rather than making multiple calls.
        - When requesting the most recent values, leave start_date and end_date empty.

        Example:
        Query: "What are the market caps of companies 6057741 and 874276?"
        Function: get_capitalization(capitalization=Capitalization.market_cap, company_ids=[6057741, 874276])
    """).strip()
    args_schema = GetCapitalizationFromIdentifierArgs

    def _run(
        self,
        capitalization: Capitalization,
        company_ids: list[int] | None = None,
        tickers: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, str]:

        assert tickers or company_ids, "You must pass tickers or company_ids"

        if company_ids:
            companies = [self.kfinance_client.company(company_id) for company_id in company_ids]
            identifiers: Sequence[int|str] = company_ids
            identifier_type = "company_id"
        else:
            assert tickers
            companies = [self.kfinance_client.ticker(ticker) for ticker in tickers]
            identifiers = tickers
            identifier_type = "ticker"

        results = {}
        for identifier, company in zip(identifiers, companies):
            company_dict = {
                "name": company.name,
                identifier_type: identifier
            }
            result: pd.DataFrame |None = getattr(company, capitalization.value)(
                start_date=start_date, end_date=end_date
            )

            if result is None:
                stringified_result = "unavailable"
            elif start_date == end_date is None and len(companies) > 1:
                # If more than one company was passed without start and end date,
                # assume that the caller only cares about the last known value
                stringified_result = str(result.tail(1).to_dict())
            else:
                stringified_result = result.to_markdown()

            results[str(company_dict)] = stringified_result

        return results


class GetBusinessRelationshipFromIdentifierArgs(BaseModel):
    # no description because the description for enum fields comes from the enum docstring.
    business_relationship: BusinessRelationshipType
    company_id: int | None = Field(
        description="The company_id for which the relationship should be retrieved.",
        default=None
    )
    ticker: str | None = Field(
        description="The ticker for which the relationship should be retrieved.",
        default=None
    )


class GetBusinessRelationship(KfinanceTool):
    name: str = "get_business_relationship"
    description: str = dedent("""
        Get the company_ids of current and previous companies that are relationship_type of a given identifier.

        Either company_id or ticker is required.

        Examples:
            query: "What are the current distributors of SPGI?"
            function: get_business_relationship(ticker="SPGI", business_relationship=BusinessRelationshipType.supplier)
            returns: {"current": [1, 5], "previous": [2]}
            interpretation: Companies with id 1 and 5 are current suppliers of SPGI. The company with ID 2 was previously a supplier of SPGI.

            query: "What are the previous borrowers of 21709?"
            function: get_business_relationship(company_id=21709, business_relationship=BusinessRelationshipType.borrower)
        """).strip()
    args_schema: Type[BaseModel] = GetBusinessRelationshipFromIdentifierArgs

    def _run(self,
             business_relationship: BusinessRelationshipType,
             company_id: int | None = None,
             ticker: str | None = None
         ) -> dict:
        if company_id:
            company = self.kfinance_client.company(company_id)
        else:
            company = self.kfinance_client.ticker(ticker)
        business_relationship_obj: BusinessRelationships = getattr(
            company, business_relationship.value
        )
        return {
            "current": [{"company_id": company.company_id} for company in business_relationship_obj.current],
            "previous": [{"company_id": company.company_id} for company in business_relationship_obj.previous],
        }

class GetEarningsCallDatetimes(KfinanceTool):
    name: str = "get_earnings_call_datetimes"
    description: str = dedent("""
        Get earnings call datetimes associated with a ticker or company.

        Either company_id or ticker is required.
        """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithTickerOrCompanyId

    def _run(self, ticker: str | None = None, company_id: str | None = None) -> str:
        if ticker is None and company_id is None:
            return "Please pass either a ticker or company."

        if company_id:
            company = self.kfinance_client.company(company_id)
        else:
            company = self.kfinance_client.ticker(ticker)
        earnings_call_datetimes = company.earnings_call_datetimes
        return json.dumps([dt.isoformat() for dt in earnings_call_datetimes])




class GetFinancialLineItemArgs(BaseModel):

    # Note: mypy will not enforce this literal because of the type: ignore.
    # But pydantic still uses the literal to check for allowed values and only includes
    # allowed values in generated schemas.
    line_item: Literal[tuple(LINE_ITEM_NAMES_AND_ALIASES)] = Field(  # type: ignore[valid-type]
        description="The type of financial line_item requested"
    )
    company_ids: list[int] | None = Field(default=None, description="A list of company_ids for which the line item should be retrieved")
    tickers: list[str] | None = Field(default=None, description="A list of tickers for which the line item should be retrieved.")
    period_type: PeriodType | None = Field(default=None, description="The period type")
    start_year: int | None = Field(default=None, description="The starting year for the data range")
    end_year: int | None = Field(default=None, description="The ending year for the data range")
    start_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Starting quarter")
    end_quarter: Literal[1, 2, 3, 4] | None = Field(default=None, description="Ending quarter")


class GetFinancialLineItem(KfinanceTool):
    name: str = "get_financial_line_item"
    description: str = dedent("""
        Get a financial line item for a list of tickers or company_ids.

        - When possible, pass multiple tickers or company_ids in a single call rather than making multiple calls.
        - To fetch the most recent value for the line item, leave start_year, start_quarter, end_year, and end_quarter as None.

        Example:
        Query: "What are the revenues of companies 6057741 and 874276?"
        Function: get_line_item(line_item="revenue", company_ids=[6057741, 874276])

        """).strip()
    args_schema: Type[BaseModel] = GetFinancialLineItemArgs

    def _run(
        self,
        line_item: str,
        tickers: list[str] | None = None,
        company_ids: list[int] | None = None,
        period_type: PeriodType | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        start_quarter: Literal[1, 2, 3, 4] | None = None,
        end_quarter: Literal[1, 2, 3, 4] | None = None,
    ) -> dict[str, str]:

        assert tickers or company_ids, "You must pass tickers or company_ids"

        if company_ids:
            companies = [self.kfinance_client.company(company_id) for company_id in company_ids]
            identifiers: Sequence[int|str] = company_ids
            identifier_type = "company_id"
        else:
            assert tickers
            companies = [self.kfinance_client.ticker(ticker) for ticker in tickers]
            identifiers = tickers
            identifier_type = "ticker"

        results = {}

        for company, identifier in zip(companies, identifiers):

            result = getattr(company, line_item)(
                period_type=period_type,
                start_year=start_year,
                end_year=end_year,
                start_quarter=start_quarter,
                end_quarter=end_quarter,
            )

            if result is None:
                stringified_result = "unavailable"
            elif start_year is end_year is start_quarter is end_quarter is None and len(companies) > 1:
                # If more than one company was passed without start and end date,
                # assume that the caller only cares about the last known value
                stringified_result = str(result.iloc[-1].tail(1).to_dict())
            else:
                stringified_result = result.to_markdown()

            dict_key = str({"name": company.name, identifier_type: identifier})
            results[dict_key] = stringified_result

        return results




ALL_TOOLS: list[KfinanceTool] = [
    ResolveCompanies,
    FilterCompanies,
    GetCapitalization,
    GetBusinessRelationship,
    GetEarningsCallDatetimes,
    GetFinancialLineItem
]
