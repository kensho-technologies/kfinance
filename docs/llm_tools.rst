llm_tools
#####################

.. py:class:: Model

    Enum with values ANTHROPIC, GEMINI, OPENAI

.. py:function:: _get_tool_dict_description(tool_name: 'str') -> 'str'

    Extracts description from the llm tool dict matching the input name

.. py:function:: _llm_tool_metadata() -> 'dict'

    The Argument schema for each of the LLM Tools

.. py:function:: _llm_tools(self: 'Client') -> 'dict[str, Callable]'

    Get AI tools initiated with Client. Outputs a dictionary mapping a function name to function

.. py:function:: _tool_descriptions(model: 'Model') -> 'list[dict]'

    Get tool descriptions for a model

.. py:function:: get_business_relationship_from_identifier(self: 'Client', identifier: 'str', business_relationship: 'str') -> 'dict'

    Get the current and previous company IDs having a business relationship with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        business_relationship: the type of business relationship requested


.. py:function:: get_company_id_from_identifier(self: 'Client', identifier: 'str') -> 'int'

    Get the company id associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.


.. py:function:: get_cusip_from_ticker(self: 'Client', ticker_str: 'str') -> 'str'

    Get the CUSIP associated with a ticker, can also be an ISIN.

    Args:
        ticker_str: The ticker


.. py:function:: get_earnings_call_datetimes_from_identifier(self: 'Client', identifier: 'str') -> 'str'

    Get earnings call datetimes associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.


.. py:function:: get_financial_line_item_from_identifier(self: 'Client', identifier: 'str', line_item: 'str', period_type: 'str | None' = None, start_year: 'int | None' = None, end_year: 'int | None' = None, start_quarter: 'int | None' = None, end_quarter: 'int | None' = None) -> 'str'

    Get the financial line item associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        line_item: The type of financial line_item requested
        period_type: time period type, valid inputs are ["annual", "quarterly", "ltm", "ytd"]
        start_quarter: starting quarter, valid inputs are [1, 2, 3, 4]
        end_quarter: ending quarter, valid inputs are [1, 2, 3, 4]
        start_year: The starting year for the data range.
        end_year: The ending year for the data range.


.. py:function:: get_financial_statement_from_identifier(self: 'Client', identifier: 'str', statement: 'str', period_type: 'str | None' = None, start_year: 'int | None' = None, end_year: 'int | None' = None, start_quarter: 'int | None' = None, end_quarter: 'int | None' = None) -> 'str'

    Get the financial statement associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        statement: The type of financial statement, valid inputs are ["balance_sheet", "income_statement", "cashflow"]
        period_type: time period type, valid inputs are ["annual", "quarterly", "ltm", "ytd"].
        start_quarter: starting quarter, valid inputs are [1, 2, 3, 4]
        end_quarter: ending quarter, valid inputs are [1, 2, 3, 4]
        start_year: The starting year for the data range.
        end_year: The ending year for the data range.


.. py:function:: get_history_metadata_from_identifier(self: 'Client', identifier: 'str') -> 'HistoryMetadata'

    Get the history metadata associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    History metadata includes currency, symbol, exchange name, instrument type, and first trade date

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.


.. py:function:: get_info_from_identifier(self: 'Client', identifier: 'str') -> 'str'

    Get the information associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Info includes company name, status, type, simple industry, number of employees, founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.


.. py:function:: get_isin_from_ticker(self: 'Client', ticker_str: 'str') -> 'str'

    Get the ISIN associated with a ticker, can also be CUSIP.

    Args:
        ticker_str: The ticker


.. py:function:: get_latest(use_local_timezone: 'bool' = True) -> 'LatestPeriods'

    Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date. The output is a dictionary with the following schema::


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


.. py:function:: get_n_quarters_ago(n: 'int') -> 'YearAndQuarter'

    Get the year and quarter corresponding to [n] quarters before the current quarter. The output is a dictionary with the following schema::


            {
                "year": int,
                "quarter": int
            }

            Args:
                n: number of quarters before the current quarter


.. py:function:: get_prices_from_identifier(self: 'Client', identifier: 'str', periodicity: 'str' = 'day', adjusted: 'bool' = True, start_date: 'str | None' = None, end_date: 'str | None' = None) -> 'str'

    Get the historical open, high, low, and close prices, and volume of an identifier, where the identifier can be a ticker, ISIN or CUSIP, between inclusive start_date and inclusive end date.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.
        start_date: The start date for historical price retrieval in format YYYY-MM-DD
        end_date: The end date for historical price retrieval in format YYYY-MM-DD
        periodicity: The frequency or interval at which the historical data points are sampled or aggregated. Periodicity is not the same as the date range. The date range specifies the time span over which the data is retrieved, while periodicity determines how the data within that date range is aggregated, valid inputs are ["day", "week", "month", "year"].
        adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits.


.. py:function:: get_security_id_from_identifier(self: 'Client', identifier: 'str') -> 'int'

    Get the security id associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.


.. py:function:: get_trading_item_id_from_identifier(self: 'Client', identifier: 'str') -> 'int'

    Get the trading item id associated with an identifier, where the identifier can be a ticker, ISIN or CUSIP.

    Args:
        identifier: A unique identifier, which can be a ticker symbol, ISIN, or CUSIP.


.. py:function:: langchain_tools(tools: 'dict[str, Callable]') -> 'list[StructuredTool]'

    Returns Langchain Tool callables

    The Tool names and descriptions sent to the LLM are taken from the base tool dict.
    The Tool arguments and arg descriptions are taken from the Pydantic models with an
    input model corresponding to each tool. Any change to the base tool dict must be reflected
    in the input model

    Args:
        tools: mapping of tool names and tool callables, to be converted to langchain tools

