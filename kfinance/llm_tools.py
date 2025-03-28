from __future__ import annotations

import copy
import datetime
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Callable, Literal

from langchain_core.tools import StructuredTool

from . import tool_schemas
from .constants import (
    LINE_ITEM_NAMES_AND_ALIASES,
    BusinessRelationshipType,
    HistoryMetadata,
    LatestPeriods,
    YearAndQuarter,
)


if TYPE_CHECKING:
    from .kfinance import BusinessRelationships, Client


class Model(Enum):
    """Enum with values ANTHROPIC, GEMINI, OPENAI"""

    ANTHROPIC = 1
    GEMINI = 2
    OPENAI = 3


def get_latest(use_local_timezone: bool = True) -> LatestPeriods:
    """Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date. The output is a dictionary with the following schema::

    {
        "annual": {
            "latest_year": int
        },
        "quarterly": {
            "latest_quarter": int,
            "latest_year": int
        },
        "now": {
            "current_year": int,
            "current_quarter": int,
            "current_month": int,
            "current_date": str # in format Y-m-d
        }
    }

    Args:
        use_local_timezone: whether to use the local timezone of the user
    """
    datetime_now = (
        datetime.datetime.now()
        if use_local_timezone
        else datetime.datetime.now(datetime.timezone.utc)
    )

    current_year = datetime_now.year
    current_qtr = (datetime_now.month - 1) // 3 + 1
    # Quarterly data most recent year and quarter
    if current_qtr == 1:
        most_recent_year_qtrly = current_year - 1
        most_recent_qtr = 4
    else:
        most_recent_year_qtrly = current_year
        most_recent_qtr = current_qtr - 1

    # Annual data most recent year
    most_recent_year_annual = current_year - 1

    current_month = datetime_now.month
    latest: LatestPeriods = {
        "annual": {"latest_year": most_recent_year_annual},
        "quarterly": {"latest_quarter": most_recent_qtr, "latest_year": most_recent_year_qtrly},
        "now": {
            "current_year": current_year,
            "current_quarter": current_qtr,
            "current_month": current_month,
            "current_date": datetime_now.strftime("%Y-%m-%d"),
        },
    }
    return latest


def get_n_quarters_ago(n: int) -> YearAndQuarter:
    """Get the year and quarter corresponding to [n] quarters before the current quarter. The output is a dictionary with the following schema::

    {
        "year": int,
        "quarter": int
    }

    Args:
        n: number of quarters before the current quarter
    """
    datetime_now = datetime.datetime.now()
    current_qtr = (datetime_now.month - 1) // 3 + 1
    total_quarters_completed = datetime_now.year * 4 + current_qtr - 1
    total_quarters_completed_n_quarters_ago = total_quarters_completed - n

    year_n_quarters_ago = total_quarters_completed_n_quarters_ago // 4
    quarter_n_quarters_ago = total_quarters_completed_n_quarters_ago % 4 + 1

    year_quarter_n_quarters_ago: YearAndQuarter = {
        "year": year_n_quarters_ago,
        "quarter": quarter_n_quarters_ago,
    }

    return year_quarter_n_quarters_ago


def get_company_id_from_identifier(self: Client, identifier: str) -> int:
    """Get the company id associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
    """
    return self.ticker(identifier).company_id


def get_security_id_from_identifier(self: Client, identifier: str) -> int:
    """Get the security id associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
    """
    return self.ticker(identifier).security_id


def get_trading_item_id_from_identifier(self: Client, identifier: str) -> int:
    """Get the trading item id associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
    """
    return self.ticker(identifier).trading_item_id


def get_isin_from_ticker(self: Client, ticker_str: str) -> str:
    """Get the ISIN associated with a ticker, can also be CUSIP.

    Args:
        ticker_str: The ticker
    """
    return self.ticker(ticker_str).isin


def get_cusip_from_ticker(self: Client, ticker_str: str) -> str:
    """Get the CUSIP associated with a ticker, can also be an ISIN.

    Args:
        ticker_str: The ticker
    """
    return self.ticker(ticker_str).cusip


def get_info_from_identifier(self: Client, identifier: str) -> str:
    """Get the information associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Info includes company name, status, type, simple industry, number of employees, founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
    """
    return str(self.ticker(identifier).info)


def get_earnings_call_datetimes_from_identifier(self: Client, identifier: str) -> str:
    """Get earnings call datetimes associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
    """
    return str(self.ticker(identifier).earnings_call_datetimes)


def get_history_metadata_from_identifier(self: Client, identifier: str) -> HistoryMetadata:
    """Get the history metadata associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    History metadata includes currency, symbol, exchange name, instrument type, and first trade date

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
    """
    return self.ticker(identifier).history_metadata


def get_prices_from_identifier(
    self: Client,
    identifier: str,
    periodicity: str = "day",
    adjusted: bool = True,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get the historical open, high, low, and close prices, and volume of an identifier, where the identifier can be a ticker, ISIN or CUSIP, between inclusive start_date and inclusive end date.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        start_date: The start date for historical price retrieval in format YYYY-MM-DD
        end_date: The end date for historical price retrieval in format YYYY-MM-DD
        periodicity: The frequency or interval at which the historical data points are sampled or aggregated. Periodicity is not the same as the date range. The date range specifies the time span over which the data is retrieved, while periodicity determines how the data within that date range is aggregated, valid inputs are ["day", "week", "month", "year"].
        adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits.
    """
    return (
        self.ticker(identifier).history(periodicity, adjusted, start_date, end_date).to_markdown()
    )


def get_capitalization_from_identifier(
    self: Client,
    identifier: str,
    capitalization: Literal["market_cap", "tev", "shares_outstanding"],
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get the historical market cap, tev (Total Enterprise Value), or shares outstanding of an identifier, where the identifier can be a ticker, ISIN or CUSIP, between inclusive start_date and inclusive end date.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        capitalization: The capitalization to retrieve (market_cap, tev, or shares_outstanding)
        start_date: The start date for historical price retrieval in format YYYY-MM-DD
        end_date: The end date for historical price retrieval in format YYYY-MM-DD
    """
    ticker = self.ticker(identifier)
    capitalization_to_func: dict[Literal["market_cap", "tev", "shares_outstanding"], Callable] = {
        "market_cap": ticker.market_cap,
        "tev": ticker.tev,
        "shares_outstanding": ticker.shares_outstanding,
    }
    func = capitalization_to_func[capitalization]
    return func(start_date=start_date, end_date=end_date).to_markdown()


def get_financial_statement_from_identifier(
    self: Client,
    identifier: str,
    statement: str,
    period_type: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: int | None = None,
    end_quarter: int | None = None,
) -> str:
    """Get the financial statement associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        statement: The type of financial statement, valid inputs are ["balance_sheet", "income_statement", "cashflow"]
        period_type: time period type, valid inputs are ["annual", "quarterly", "ltm", "ytd"].
        start_quarter: starting quarter, valid inputs are [1, 2, 3, 4]
        end_quarter: ending quarter, valid inputs are [1, 2, 3, 4]
        start_year: The starting year for the data range.
        end_year: The ending year for the data range.
    """
    return getattr(self.ticker(identifier), statement)(
        period_type, start_year, end_year, start_quarter, end_quarter
    ).to_markdown()


def get_financial_line_item_from_identifier(
    self: Client,
    identifier: str,
    line_item: str,
    period_type: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    start_quarter: int | None = None,
    end_quarter: int | None = None,
) -> str:
    """Get the financial line item associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        line_item: The type of financial line_item requested
        period_type: time period type, valid inputs are ["annual", "quarterly", "ltm", "ytd"]
        start_quarter: starting quarter, valid inputs are [1, 2, 3, 4]
        end_quarter: ending quarter, valid inputs are [1, 2, 3, 4]
        start_year: The starting year for the data range.
        end_year: The ending year for the data range.
    """
    return getattr(self.ticker(identifier), line_item)(
        period_type, start_year, end_year, start_quarter, end_quarter
    ).to_markdown()


def get_business_relationship_from_identifier(
    self: Client, identifier: str, business_relationship: str
) -> dict:
    """Get the current and previous company IDs having a business relationship with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        business_relationship: the type of business relationship requested
    """
    business_relationship_obj: "BusinessRelationships" = getattr(
        self.ticker(identifier), business_relationship
    )
    return {
        "current": [company.company_id for company in business_relationship_obj.current],
        "previous": [company.company_id for company in business_relationship_obj.previous],
    }


def _llm_tools(self: Client) -> dict[str, Callable]:
    """Get AI tools initiated with Client. Outputs a dictionary mapping a function name to function"""

    return {
        "get_latest": get_latest,
        "get_n_quarters_ago": get_n_quarters_ago,
        "get_company_id_from_identifier": partial(get_company_id_from_identifier, self),
        "get_security_id_from_identifier": partial(get_security_id_from_identifier, self),
        "get_trading_item_id_from_identifier": partial(get_trading_item_id_from_identifier, self),
        "get_isin_from_ticker": partial(get_isin_from_ticker, self),
        "get_cusip_from_ticker": partial(get_cusip_from_ticker, self),
        "get_info_from_identifier": partial(get_info_from_identifier, self),
        "get_earnings_call_datetimes_from_identifier": partial(
            get_earnings_call_datetimes_from_identifier, self
        ),
        "get_history_metadata_from_identifier": partial(get_history_metadata_from_identifier, self),
        "get_prices_from_identifier": partial(get_prices_from_identifier, self),
        "get_capitalization_from_identifier": partial(get_capitalization_from_identifier, self),
        "get_financial_statement_from_identifier": partial(
            get_financial_statement_from_identifier, self
        ),
        "get_financial_line_item_from_identifier": partial(
            get_financial_line_item_from_identifier, self
        ),
        "get_business_relationship_from_identifier": partial(
            get_business_relationship_from_identifier, self
        ),
    }


def _llm_tool_metadata() -> dict:
    """The Argument schema for each of the LLM Tools"""
    return {
        "get_latest": tool_schemas.GetLatestInput,
        "get_n_quarters_ago": tool_schemas.GetNQuartersAgoInput,
        "get_company_id_from_identifier": tool_schemas.GetCompanyIdFromIdentifier,
        "get_security_id_from_identifier": tool_schemas.GetSecurityIdFromIdentifier,
        "get_trading_item_id_from_identifier": tool_schemas.GetTradingItemIdFromIdentifier,
        "get_isin_from_ticker": tool_schemas.GetIsinFromTicker,
        "get_cusip_from_ticker": tool_schemas.GetCusipFromTicker,
        "get_info_from_identifier": tool_schemas.GetInfoFromIdentifier,
        "get_earnings_call_datetimes_from_identifier": tool_schemas.GetEarningsCallDatetimesFromIdentifier,
        "get_history_metadata_from_identifier": tool_schemas.GetHistoryMetadataFromIdentifier,
        "get_prices_from_identifier": tool_schemas.GetPricesFromIdentifier,
        "get_capitalization_from_identifier": tool_schemas.GetCapitalizationFromIdentifier,
        "get_financial_statement_from_identifier": tool_schemas.GetFinancialStatementFromIdentifier,
        "get_financial_line_item_from_identifier": tool_schemas.GetFinancialLineItemFromIdentifier,
        "get_business_relationship_from_identifier": tool_schemas.GetBusinessRelationshipFromIdentifier,
    }


_base_tool_descriptions = [
    {
        "name": "get_latest",
        "description": """Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date. The output is a dictionary with the following schema:
        {
            "annual": {
                "latest_year": int
            },
            "quarterly": {
                "latest_quarter": int,
                "latest_year": int
            },
            "now": {
                "current_year": int,
                "current_quarter": int,
                "current_month": int,
                "current_date": str # in format Y-m-d
            }
        }""",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_n_quarters_ago",
        "description": """Get the year and quarter corresponding to [n] quarters before the current quarter. The output is a dictionary with the following schema::
        {
            "year": int,
            "quarter": int
        }
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "description": "The number of quarters before the current quarter to retrieve the corresponding year and quarter",
                },
            },
            "required": ["n"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_company_id_from_identifier",
        "description": "Get the company id associated with an identifier",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_security_id_from_ticker",
        "description": "Get the security id associated with an identifier",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_trading_item_id_from_ticker",
        "description": "Get the trading item id associated with an identifier",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_isin_from_ticker",
        "description": "Get the ISIN associated with a ticker",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker_str": {"type": "string", "description": "The ticker"},
            },
            "required": ["ticker_str"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_cusip_from_ticker",
        "description": "Get the CUSIP associated with a ticker",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker_str": {"type": "string", "description": "The ticker"},
            },
            "required": ["ticker_str"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_info_from_identifier",
        "description": "Get the information associated with an identifier. Info includes company name, status, type, simple industry, number of employees, founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_earnings_call_datetimes_from_identifier",
        "description": "Get the earnings call datetimes of an identifier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_history_metadata_from_identifier",
        "description": "Get the history metadata associated with an identifier. History metadata includes currency, symbol, exchange name, instrument type, and first trade date",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_prices_from_identifier",
        "description": "Get the historical open, high, low, and close prices, and volume of an identifier, where the identifier can be a ticker, ISIN or CUSIP, between inclusive start_date and inclusive end date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
                "start_date": {
                    "type": "string",
                    "description": "The start date for historical price retrieval in format YYYY-MM-DD",
                },
                "end_date": {
                    "type": "string",
                    "description": "The end date for historical price retrieval in format YYYY-MM-DD",
                },
                "periodicity": {
                    "type": "string",
                    "description": "The frequency or interval at which the historical data points are sampled or aggregated. Periodicity is not the same as the date range. The date range specifies the time span over which the data is retrieved, while periodicity determines how the data within that date range is aggregated.",
                    "enum": ["day", "week", "month", "year", "none"],
                },
                "adjusted": {
                    "type": "boolean",
                    "description": "Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits.",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_capitalization_from_identifier",
        "description": "Get the historical market cap, tev (Total Enterprise Value), or shares outstanding of an identifier, where the identifier can be a ticker, ISIN or CUSIP, between inclusive start_date and inclusive end date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
                "capitalization": {
                    "type": "string",
                    "description": "The capitalization to retrieve (market_cap, tev, or shares_outstanding).",
                    "enum": ["market_cap", "tev", "shares_outstanding"],
                },
                "start_date": {
                    "type": "string",
                    "description": "The start date for historical price retrieval in format YYYY-MM-DD",
                },
                "end_date": {
                    "type": "string",
                    "description": "The end date for historical price retrieval in format YYYY-MM-DD",
                },
            },
            "required": ["identifier", "capitalization"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_financial_statement_from_identifier",
        "description": "Get the financial statement associated with an identifier",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
                "statement": {
                    "type": "string",
                    "description": "The type of financial statement",
                    "enum": ["balance_sheet", "income_statement", "cashflow"],
                },
                "period_type": {
                    "type": "string",
                    "enum": ["annual", "quarterly", "ltm", "ytd"],
                },
                "start_quarter": {"type": "integer", "enum": [1, 2, 3, 4]},
                "end_quarter": {"type": "integer", "enum": [1, 2, 3, 4]},
                "start_year": {
                    "type": "integer",
                    "description": "The starting year for the data range.",
                },
                "end_year": {
                    "type": "integer",
                    "description": "The ending year for the data range.",
                },
            },
            "required": ["identifier", "statement"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_financial_line_item_from_identifier",
        "description": 'Get the financial line item associated with an identifier. Used to answer questions about specific line items. For example, "Honda\'s finance division other non-current assets at the year-end 2021." or "Builders FirstSource\'s repayments of long-term debt in 2022 and impact on debt-to-equity" ',
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
                "line_item": {
                    "type": "string",
                    "description": "The type of financial line_item requested",
                    "enum": LINE_ITEM_NAMES_AND_ALIASES,
                },
                "period_type": {
                    "type": "string",
                    "enum": ["annual", "quarterly", "ltm", "ytd"],
                },
                "start_quarter": {"type": "integer", "enum": [1, 2, 3, 4]},
                "end_quarter": {"type": "integer", "enum": [1, 2, 3, 4]},
                "start_year": {
                    "type": "integer",
                    "description": "The starting year for the data range.",
                },
                "end_year": {
                    "type": "integer",
                    "description": "The ending year for the data range.",
                },
            },
            "required": ["identifier", "line_item"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_business_relationship_from_identifier",
        "description": 'Get the current and previous company IDs that are relationship_type of a given identifier. For example, "What are the current distributors of SPGI?" or "What are the previous borrowers of JPM?" ',
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.",
                },
                "business_relationship": {
                    "type": "string",
                    "description": "The type of business relationship requested",
                    "enum": list(BusinessRelationshipType.__members__.keys()),
                },
            },
            "required": ["identifier", "business_relationship"],
            "additionalProperties": False,
        },
    },
]


def _get_tool_dict_description(tool_name: str) -> str:
    """Extracts description from the llm tool dict matching the input name"""
    for tool_dict in _base_tool_descriptions:
        if tool_dict["name"] == tool_name:
            return str(tool_dict["description"])
    return ""


def _tool_descriptions(model: Model) -> list[dict]:
    """Get tool descriptions for a model"""

    def change_base_tool_descriptions_schema_for_openai(tool_description: dict) -> dict:
        new_tool_description = copy.deepcopy(tool_description)
        new_tool_description["parameters"] = new_tool_description.pop("input_schema")
        return {"type": "function", "function": new_tool_description}

    def change_base_tool_descriptions_schema_for_gemini(tool_description: dict) -> dict:
        new_tool_description = copy.deepcopy(tool_description)
        new_tool_description["parameters"] = new_tool_description.pop("input_schema")
        if "additionalProperties" in new_tool_description["parameters"].keys():
            del new_tool_description["parameters"]["additionalProperties"]
        for tool_property in new_tool_description["parameters"]["properties"].values():
            if "enum" in tool_property.keys() and tool_property["type"] == "integer":
                del tool_property["enum"]
        if new_tool_description["parameters"]["properties"] == {}:
            del new_tool_description["parameters"]
        return new_tool_description

    if model == Model.OPENAI:
        return list(
            map(
                change_base_tool_descriptions_schema_for_openai,
                _base_tool_descriptions,
            )
        )
    elif model == Model.GEMINI:
        return [
            {
                "function_declarations": list(
                    map(change_base_tool_descriptions_schema_for_gemini, _base_tool_descriptions)
                )
            }
        ]

    elif model == Model.ANTHROPIC:
        return _base_tool_descriptions
    else:
        raise NotImplementedError(f"tool descriptions for model: {model} have not been implemented")


def langchain_tools(tools: dict[str, Callable]) -> list[StructuredTool]:
    """Returns Langchain Tool callables

    The Tool names and descriptions sent to the LLM are taken from the base tool dict.
    The Tool arguments and arg descriptions are taken from the Pydantic models with an
    input model corresponding to each tool. Any change to the base tool dict must be reflected
    in the input model

    Args:
        tools: mapping of tool names and tool callables, to be converted to langchain tools
    """
    all_tools = []
    for tool_name, tool_callable in tools.items():
        schemas = _llm_tool_metadata()
        tool_description = _get_tool_dict_description(tool_name=tool_name)
        langchain_tool = StructuredTool.from_function(
            func=tool_callable,
            name=tool_name,
            description=tool_description,
            args_schema=schemas[tool_name],
            infer_schema=False,
        )
        all_tools.append(langchain_tool)
    return all_tools


gemini_tool_descriptions = _tool_descriptions(Model.GEMINI)
openai_tool_descriptions = _tool_descriptions(Model.OPENAI)
anthropic_tool_descriptions = _tool_descriptions(Model.ANTHROPIC)
