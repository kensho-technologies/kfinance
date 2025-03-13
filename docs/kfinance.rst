kfinance
#####################

.. py:class:: BusinessRelationships

    Business relationships object that represents the current and previous companies of a given Company object.

    :param current: A Companies set that represents the current company_ids.
    :param previous: A Companies set that represents the previous company_ids.


    .. py:function:: __getnewargs__(self)

        Return self as a plain tuple.  Used by copy and pickle.

    .. py:function:: __new__(_cls, current: ForwardRef('Companies'), previous: ForwardRef('Companies'))

        Create new instance of BusinessRelationships(current, previous)

    .. py:function:: __repr__(self)

        Return a nicely formatted representation string

    .. py:function:: __str__(self) -> 'str'

        String representation for the BusinessRelationships object

    .. py:function:: _asdict(self)

        Return a new dict which maps field names to their values.

    .. py:function:: _replace(self, /, **kwds)

        Return a new BusinessRelationships object replacing specified fields with new values

.. py:class:: Client

    Client class with LLM tools and a pre-credentialed Ticker object

    :param tools: A dictionary mapping function names to functions, where each function is an llm tool with the Client already passed in if applicable
    :type tools: dict[str, Callable]
    :param anthropic_tool_descriptions: A list of dictionaries, where each dictionary is an Anthropic tool definition
    :type anthropic_tool_descriptions: list[dict]
    :param gemini_tool_descriptions: A dictionary mapping "function_declarations" to a list of dictionaries, where each dictionary is a Gemini tool definition
    :type gemini_tool_descriptions: dict[list[dict]]
    :param openai_tool_descriptions: A list of dictionaries, where each dictionary is an OpenAI tool definition
    :type openai_tool_descriptions: list[dict]


    .. py:function:: __init__(self, refresh_token: 'Optional[str]' = None, client_id: 'Optional[str]' = None, private_key: 'Optional[str]' = None, api_host: 'str' = 'https://kfinance.kensho.com', api_version: 'int' = 1, okta_host: 'str' = 'https://kensho.okta.com', okta_auth_server: 'str' = 'default')

        Initialization of the client.

        :param refresh_token: users refresh token
        :type refresh_token: str, Optional
        :param client_id: users client id will be provided by support@kensho.com
        :type client_id: str, Optional
        :param private_key: users private key that corresponds to the registered public sent to support@kensho.com
        :type private_key: str, Optional
        :param api_host: the api host URL
        :type api_host: str
        :param api_version: the api version number
        :type api_version: int
        :param okta_host: the okta host URL
        :type okta_host: str
        :param okta_auth_server: the okta route for authentication
        :type okta_auth_server: str


    .. py:function:: company(self, company_id: 'int') -> 'Company'

        Generate the Company object from company_id

        :param company_id: CIQ company id
        :type company_id: int
        :return: The Company specified by the the company id
        :rtype: Company


    .. py:function:: get_latest() -> 'LatestPeriods'

        Get the latest annual reporting year, latest quarterly reporting quarter and year, and current date.

        :return: A dict in the form of {"annual": {"latest_year": int}, "quarterly": {"latest_quarter": int, "latest_year": int}, "now": {"current_year": int, "current_quarter": int, "current_month": int, "current_date": str of Y-m-d}}
        :rtype: Latest


    .. py:function:: get_n_quarters_ago(n: 'int') -> 'YearAndQuarter'

        Get the year and quarter corresponding to [n] quarters before the current quarter

        :param int n: the number of quarters before the current quarter
        :return: A dict in the form of {"year": int, "quarter": int}
        :rtype: YearAndQuarter


    .. py:function:: security(self, security_id: 'int') -> 'Security'

        Generate Security object from security_id

        :param security_id: CIQ security id
        :type security_id: int
        :return: The Security specified by the the security id
        :rtype: Security


    .. py:function:: ticker(self, identifier: 'int | str', exchange_code: 'Optional[str]' = None, function_called: 'Optional[bool]' = False) -> 'Ticker'

        Generate Ticker object from [identifier] that is a ticker, ISIN, or CUSIP.

        :param  identifier: the ticker symbol, ISIN, or CUSIP
        :type identifier: str
        :param exchange_code: The code representing the equity exchange the ticker is listed on.
        :type exchange_code: str, optional
        :param function_called: Flag for use in signaling function calling
        :type function_called: bool, optional
        :return: Ticker object from that corresponds to the identifier
        :rtype: Ticker


    .. py:function:: tickers(self, country_iso_code: 'Optional[str]' = None, state_iso_code: 'Optional[str]' = None, simple_industry: 'Optional[str]' = None, exchange_code: 'Optional[str]' = None) -> 'Tickers'

        Generate tickers object representing the collection of Tickers that meet all the supplied parameters

        One of country_iso_code, simple_industry, or exchange_code must be supplied. A parameter set to None is not used to filter on

        :param country_iso_code: The ISO 3166-1 Alpha-2 or Alpha-3 code that represent the primary country the firm is based in. It default None
        :type country_iso_code: str, optional
        :param state_iso_code: The ISO 3166-2 Alpha-2 code that represents the primary subdivision of the country the firm the based in. Not all ISO 3166-2 codes are supported as S&P doesn't maintain the full list but a feature request for the full list is submitted to S&P product. Requires country_iso_code also to have a value other then None. It default None
        :type state_iso_code: str, optional
        :param simple_industry: The S&P CIQ Simple Industry defined in ciqSimpleIndustry in XPF. It default None
        :type simple_industry: str, optional
        :param exchange_code: The exchange code for the primary equity listing exchange of the firm. It default None
        :type exchange_code: str, optional
        :return: A tickers object that is the group of Ticker objects meeting all the supplied parameters
        :rtype: Tickers


    .. py:function:: trading_item(self, trading_item_id: 'int') -> 'TradingItem'

        Generate TradingItem object from trading_item_id

        :param trading_item_id: CIQ trading item id
        :type trading_item_id: int
        :return: The trading item specified by the the trading item id
        :rtype: TradingItem


.. py:class:: Companies

    Base class for representing a set of Companies

    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', company_ids: 'Iterable[int]') -> 'None'

        Initialize the Companies object

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param company_ids: An iterable of S&P CIQ Company ids
        :type company_ids: Iterable[int]


.. py:class:: Company

    Company class

    :param KFinanceApiClient kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param company_id: The S&P Global CIQ Company Id
    :type company_id: int


    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', company_id: 'int')

        Initialize the Company object

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param company_id: The S&P Global CIQ Company Id
        :type company_id: int


    .. py:function:: __str__(self) -> 'str'

        String representation for the company object

    .. py:function:: accounts_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1018

    .. py:function:: accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1021

    .. py:function:: accrued_expenses(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1016

    .. py:function:: accumulated_depreciation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1075

    .. py:function:: additional_paid_in_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1084

    .. py:function:: additional_paid_in_capital_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_additional_paid_in_capital

        ciq data item 1085

    .. py:function:: adjustments_to_cash_flow_net_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 21523

    .. py:function:: amortization_of_goodwill_and_intangibles(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 31

    .. py:function:: asset_writedown(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 32

    .. py:function:: assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_assets

        ciq data item 1007

    .. py:function:: balance_sheet(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated balance sheet

    .. py:function:: basic_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps

        ciq data item 9

    .. py:function:: basic_earning_per_share_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_excluding_extra_items

        ciq data item 3064

    .. py:function:: basic_earning_per_share_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_from_accounting_change

        ciq data item 145

    .. py:function:: basic_earning_per_share_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_from_accounting_change_and_extraordinary_items

        ciq data item 45

    .. py:function:: basic_earning_per_share_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_from_extraordinary_items

        ciq data item 146

    .. py:function:: basic_earning_per_share_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps

        ciq data item 9

    .. py:function:: basic_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 9

    .. py:function:: basic_eps_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3064

    .. py:function:: basic_eps_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 145

    .. py:function:: basic_eps_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 45

    .. py:function:: basic_eps_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 146

    .. py:function:: basic_eps_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps

        ciq data item 9

    .. py:attribute:: borrower

        Returns the associated company's current and previous borrowers

    .. py:function:: capex(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_expenditure

        ciq data item 2021

    .. py:function:: capital_expenditure(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2021

    .. py:function:: capital_expenditures(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_expenditure

        ciq data item 2021

    .. py:function:: capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1183

    .. py:function:: capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_leases

        ciq data item 1183

    .. py:function:: cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_and_equivalents

        ciq data item 1096

    .. py:function:: cash_acquisitions(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2057

    .. py:function:: cash_and_cash_equivalents(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_and_equivalents

        ciq data item 1096

    .. py:function:: cash_and_equivalents(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1096

    .. py:function:: cash_and_short_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_cash_and_short_term_investments

        ciq data item 1002

    .. py:function:: cash_flow(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated cash flow statement

    .. py:function:: cash_flow_from_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_operations

        ciq data item 2006

    .. py:function:: cash_from_discontinued_operation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_cash_from_discontinued_operation

        ciq data item 2081

    .. py:function:: cash_from_financing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2004

    .. py:function:: cash_from_financing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_financing

        ciq data item 2004

    .. py:function:: cash_from_investing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2005

    .. py:function:: cash_from_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_investing

        ciq data item 2005

    .. py:function:: cash_from_operating_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_operations

        ciq data item 2006

    .. py:function:: cash_from_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2006

    .. py:function:: cashflow(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated cash flow statement

    .. py:function:: cashflow_from_financing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_financing

        ciq data item 2004

    .. py:function:: cashflow_from_financing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_financing

        ciq data item 2004

    .. py:function:: cashflow_from_investing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_investing

        ciq data item 2005

    .. py:function:: cashflow_from_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_investing

        ciq data item 2005

    .. py:function:: change_in_accounts_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2017

    .. py:function:: change_in_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2018

    .. py:function:: change_in_cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_change_in_cash

        ciq data item 2093

    .. py:function:: change_in_deferred_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2084

    .. py:function:: change_in_income_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2101

    .. py:function:: change_in_inventories(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2099

    .. py:function:: change_in_net_operating_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2010

    .. py:function:: change_in_net_working_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4421

    .. py:function:: change_in_other_net_operating_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2045

    .. py:function:: change_in_trading_asset_securities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2134

    .. py:function:: change_in_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2139

    .. py:attribute:: client_services

        Returns the associated company's current and previous client_servicess

    .. py:function:: cogs(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cost_of_goods_sold

        ciq data item 34

    .. py:function:: common_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2074

    .. py:function:: common_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_common_equity

        ciq data item 1006

    .. py:function:: common_shares_outstanding(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1100

    .. py:function:: common_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1103

    .. py:attribute:: company_id

        Set and return the company id for the object

    .. py:function:: continued_operations_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for earnings_from_continued_operations

        ciq data item 7

    .. py:function:: convertible_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_convertible

        ciq data item 1214

    .. py:function:: cor(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cost_of_revenue

        ciq data item 1

    .. py:function:: cost_of_goods_sold(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 34

    .. py:function:: cost_of_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1

    .. py:attribute:: creditor

        Returns the associated company's current and previous creditors

    .. py:function:: currency_exchange_gains(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 38

    .. py:function:: current_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for accounts_receivable

        ciq data item 1021

    .. py:function:: current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_assets

        ciq data item 1008

    .. py:function:: current_borrowing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_borrowings

        ciq data item 1046

    .. py:function:: current_borrowings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_borrowings

        ciq data item 1046

    .. py:function:: current_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_debt_issued

        ciq data item 2043

    .. py:function:: current_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_debt_repaid

        ciq data item 2044

    .. py:function:: current_deferred_tax_asset(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for deferred_tax_asset_current_portion

        ciq data item 1117

    .. py:function:: current_deferred_tax_liability(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1119

    .. py:function:: current_income_taxes_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1094

    .. py:function:: current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_liabilities

        ciq data item 1009

    .. py:function:: current_notes_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for notes_receivable

        ciq data item 1048

    .. py:function:: current_other_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_receivables

        ciq data item 1206

    .. py:function:: current_portion_of_cap_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_capital_leases

        ciq data item 1090

    .. py:function:: current_portion_of_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1090

    .. py:function:: current_portion_of_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_capital_leases

        ciq data item 1090

    .. py:function:: current_portion_of_income_taxes_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_income_taxes_payable

        ciq data item 1094

    .. py:function:: current_portion_of_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_capital_leases

        ciq data item 1090

    .. py:function:: current_portion_of_long_term_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1297

    .. py:function:: current_portion_of_long_term_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1279

    .. py:function:: current_portion_of_long_term_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_lt_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt

        ciq data item 1297

    .. py:function:: current_portion_of_lt_debt_and_cap_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_non_current_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt

        ciq data item 1297

    .. py:function:: current_portion_of_non_current_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_non_current_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_unearned_revenue

        ciq data item 1074

    .. py:function:: current_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4030

    .. py:function:: current_total_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: current_total_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: current_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1074

    .. py:attribute:: customer

        Returns the associated company's current and previous customers

    .. py:function:: d_and_a(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for depreciation_and_amortization

        ciq data item 41

    .. py:function:: debt_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: deferred_tax_asset_current_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1117

    .. py:function:: depreciation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2143

    .. py:function:: depreciation_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 41

    .. py:function:: depreciation_of_rental_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 42409

    .. py:function:: diluted_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps

        ciq data item 8

    .. py:function:: diluted_earning_per_share_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_excluding_extra_items

        ciq data item 142

    .. py:function:: diluted_earning_per_share_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_accounting_change

        ciq data item 141

    .. py:function:: diluted_earning_per_share_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_accounting_change_and_extraordinary_items

        ciq data item 44

    .. py:function:: diluted_earning_per_share_from_discontinued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_discontinued_operations

        ciq data item 143

    .. py:function:: diluted_earning_per_share_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_extraordinary_items

        ciq data item 144

    .. py:function:: diluted_earning_per_share_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps

        ciq data item 8

    .. py:function:: diluted_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 8

    .. py:function:: diluted_eps_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 142

    .. py:function:: diluted_eps_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 141

    .. py:function:: diluted_eps_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 44

    .. py:function:: diluted_eps_from_discontinued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 143

    .. py:function:: diluted_eps_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 144

    .. py:function:: diluted_eps_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps

        ciq data item 8

    .. py:function:: discontinued_operations_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for earnings_from_discontinued_operations

        ciq data item 40

    .. py:function:: distributable_cash_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 23317

    .. py:attribute:: distributor

        Returns the associated company's current and previous distributors

    .. py:function:: divestitures(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2077

    .. py:function:: dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_dividends_paid

        ciq data item 2022

    .. py:function:: dividends_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3058

    .. py:function:: dna(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for depreciation_and_amortization

        ciq data item 41

    .. py:function:: earnings_before_interest_and_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebit

        ciq data item 400

    .. py:function:: earnings_before_interest_taxes_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebita

        ciq data item 100689

    .. py:function:: earnings_before_interest_taxes_depreciation_amortization_and_rental_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebitdar

        ciq data item 21674

    .. py:function:: earnings_before_interest_taxes_depreciation_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebitda

        ciq data item 4051

    .. py:function:: earnings_before_taxes_excluding_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebt_excluding_unusual_items

        ciq data item 4

    .. py:function:: earnings_before_taxes_including_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebt_including_unusual_items

        ciq data item 139

    .. py:attribute:: earnings_call_datetimes

        Get the datetimes of the companies earnings calls

        :return: a list of datetimes for the companies earnings calls
        :rtype: list[datetime]


    .. py:function:: earnings_from_continued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 7

    .. py:function:: earnings_from_discontinued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 40

    .. py:function:: ebit(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 400

    .. py:function:: ebita(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 100689

    .. py:function:: ebitda(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4051

    .. py:function:: ebitdar(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 21674

    .. py:function:: ebt_excluding_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4

    .. py:function:: ebt_including_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 139

    .. py:function:: effective_tax_rate(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4376

    .. py:function:: equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_equity

        ciq data item 1275

    .. py:function:: equity_adjustment_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_equity_adjustment

        ciq data item 1215

    .. py:function:: exploration_and_drilling_costs(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 49

    .. py:function:: exploration_and_drilling_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for exploration_and_drilling_costs

        ciq data item 49

    .. py:function:: extraordinary_item_and_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 42

    .. py:function:: fees_and_other_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 168

    .. py:function:: ffo(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for funds_from_operations

        ciq data item 3074

    .. py:function:: finance_division_debt_current_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1030

    .. py:function:: finance_division_debt_long_term_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_debt_non_current_portion

        ciq data item 1035

    .. py:function:: finance_division_debt_non_current_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1035

    .. py:function:: finance_division_interest_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 50

    .. py:function:: finance_division_loans_and_leases_long_term(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1033

    .. py:function:: finance_division_loans_and_leases_short_term(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1032

    .. py:function:: finance_division_long_term_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_debt_non_current_portion

        ciq data item 1035

    .. py:function:: finance_division_long_term_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_long_term

        ciq data item 1033

    .. py:function:: finance_division_non_current_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_debt_non_current_portion

        ciq data item 1035

    .. py:function:: finance_division_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 51

    .. py:function:: finance_division_other_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1029

    .. py:function:: finance_division_other_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1031

    .. py:function:: finance_division_other_long_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_assets

        ciq data item 1034

    .. py:function:: finance_division_other_long_term_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_liabilities

        ciq data item 1036

    .. py:function:: finance_division_other_non_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1034

    .. py:function:: finance_division_other_non_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1036

    .. py:function:: finance_division_other_short_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_current_assets

        ciq data item 1029

    .. py:function:: finance_division_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 52

    .. py:function:: finance_division_short_term_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_short_term

        ciq data item 1032

    .. py:function:: foreign_exchange_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for foreign_exchange_rate_adjustments

        ciq data item 2144

    .. py:function:: foreign_exchange_rate_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2144

    .. py:attribute:: franchisee

        Returns the associated company's current and previous franchisees

    .. py:attribute:: franchisor

        Returns the associated company's current and previous franchisors

    .. py:function:: funds_from_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3074

    .. py:function:: fx_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for foreign_exchange_rate_adjustments

        ciq data item 2144

    .. py:function:: gain_from_sale_of_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 62

    .. py:function:: gain_from_sale_of_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 56

    .. py:function:: goodwill(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1171

    .. py:function:: gppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for gross_property_plant_and_equipment

        ciq data item 1169

    .. py:function:: gross_ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for gross_property_plant_and_equipment

        ciq data item 1169

    .. py:function:: gross_profit(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 10

    .. py:function:: gross_property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1169

    .. py:function:: impairment_o_and_g(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for impairment_of_oil_gas_and_mineral_properties

        ciq data item 71

    .. py:function:: impairment_of_goodwill(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 209

    .. py:function:: impairment_of_oil_and_gas(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for impairment_of_oil_gas_and_mineral_properties

        ciq data item 71

    .. py:function:: impairment_of_oil_gas_and_mineral_properties(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 71

    .. py:function:: in_process_r_and_d_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_r_and_d_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_research_and_development_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_research_and_development_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 72

    .. py:function:: in_process_rnd_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_rnd_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: income_from_affiliates(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 47

    .. py:function:: income_statement(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated income statement

    .. py:function:: income_stmt(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated income statement

    .. py:function:: income_tax(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for income_tax_expense

        ciq data item 75

    .. py:function:: income_tax_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 75

    .. py:function:: income_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for income_tax_expense

        ciq data item 75

    .. py:attribute:: info

        Get the company info

        :return: a dict with containing: name, status, type, simple industry, number of employees, founding date, webpage, address, city, zip code, state, country, & iso_country
        :rtype: dict


    .. py:function:: insurance_division_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 69

    .. py:function:: insurance_division_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 70

    .. py:function:: insurance_settlements(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 73

    .. py:function:: interest_and_investment_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 65

    .. py:function:: interest_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 82

    .. py:function:: interest_expense_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_interest_expense

        ciq data item 50

    .. py:function:: inventories(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for inventory

        ciq data item 1043

    .. py:function:: inventory(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1043

    .. py:attribute:: investor_relations_client

        Returns the associated company's current and previous investor_relations_clients

    .. py:attribute:: investor_relations_firm

        Returns the associated company's current and previous investor_relations_firms

    .. py:function:: issuance_of_common_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2169

    .. py:function:: issuance_of_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2181

    .. py:attribute:: landlord

        Returns the associated company's current and previous landlords

    .. py:attribute:: latest_earnings_call

        Set and return the latest earnings call item for the object

        :raises NotImplementedError: This function is not yet implemented


    .. py:function:: legal_settlements(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 77

    .. py:attribute:: lessee

        Returns the associated company's current and previous lessees

    .. py:attribute:: lessor

        Returns the associated company's current and previous lessors

    .. py:function:: liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_liabilities

        ciq data item 1276

    .. py:function:: liabilities_and_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_liabilities_and_equity

        ciq data item 1013

    .. py:attribute:: licensee

        Returns the associated company's current and previous licensees

    .. py:attribute:: licensor

        Returns the associated company's current and previous licensors

    .. py:function:: line_item(self, line_item: str, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        Get a DataFrame of a financial line item according to the date ranges.

    .. py:function:: loans_held_for_sale(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1185

    .. py:function:: loans_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_loans_receivable

        ciq data item 1050

    .. py:function:: long_term_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1088

    .. py:function:: long_term_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1049

    .. py:function:: long_term_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2034

    .. py:function:: long_term_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2036

    .. py:function:: long_term_deferred_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1025

    .. py:function:: long_term_deferred_tax_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1026

    .. py:function:: long_term_finance_division_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_long_term

        ciq data item 1033

    .. py:function:: long_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1054

    .. py:function:: long_term_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_leases

        ciq data item 1183

    .. py:function:: long_term_loans_and_leases_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_long_term

        ciq data item 1033

    .. py:function:: long_term_loans_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1050

    .. py:function:: long_term_other_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_long_term_assets

        ciq data item 1060

    .. py:function:: long_term_other_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_non_current_liabilities

        ciq data item 1062

    .. py:function:: long_term_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for non_current_unearned_revenue

        ciq data item 1256

    .. py:function:: loss_on_equity_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2086

    .. py:function:: merger_and_restructuring_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 363

    .. py:function:: merger_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 80

    .. py:function:: minority_interest_in_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 83

    .. py:function:: misc_cash_flow_adj(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for miscellaneous_cash_flow_adjustments

        ciq data item 2149

    .. py:function:: miscellaneous_cash_flow_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2149

    .. py:function:: net_cash_from_discontinued_operation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2081

    .. py:function:: net_cash_from_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2027

    .. py:function:: net_change_in_cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2093

    .. py:function:: net_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4364

    .. py:function:: net_decrease_in_investment_loans_originated_and_sold(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2032

    .. py:function:: net_decrease_in_loans_originated_and_sold(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2033

    .. py:function:: net_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 15

    .. py:function:: net_income_allocable_to_general_partner(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 249

    .. py:function:: net_income_to_common_shareholders_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 379

    .. py:function:: net_income_to_common_shareholders_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 16

    .. py:function:: net_income_to_company(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 41571

    .. py:function:: net_income_to_minority_interest(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for minority_interest_in_earnings

        ciq data item 83

    .. py:function:: net_interest_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 368

    .. py:function:: net_ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: net_property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1004

    .. py:function:: net_working_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1311

    .. py:function:: non_current_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_accounts_receivable

        ciq data item 1088

    .. py:function:: non_current_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_debt

        ciq data item 1049

    .. py:function:: non_current_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_debt_issued

        ciq data item 2034

    .. py:function:: non_current_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_debt_repaid

        ciq data item 2036

    .. py:function:: non_current_deferred_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_deferred_charges

        ciq data item 1025

    .. py:function:: non_current_deferred_tax_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_deferred_tax_assets

        ciq data item 1026

    .. py:function:: non_current_deferred_tax_liability(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1027

    .. py:function:: non_current_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_investments

        ciq data item 1054

    .. py:function:: non_current_loans_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_loans_receivable

        ciq data item 1050

    .. py:function:: non_current_other_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_long_term_assets

        ciq data item 1060

    .. py:function:: non_current_other_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_non_current_liabilities

        ciq data item 1062

    .. py:function:: non_current_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1256

    .. py:function:: non_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_non_redeemable

        ciq data item 1216

    .. py:function:: normal_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for revenue

        ciq data item 112

    .. py:function:: normalized_basic_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for normalized_basic_eps

        ciq data item 4379

    .. py:function:: normalized_basic_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4379

    .. py:function:: normalized_diluted_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for normalized_diluted_eps

        ciq data item 4380

    .. py:function:: normalized_diluted_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4380

    .. py:function:: notes_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1048

    .. py:function:: nppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_operating_expense

        ciq data item 373

    .. py:function:: operating_expense_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_operating_expense

        ciq data item 51

    .. py:function:: operating_expense_insurance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for insurance_division_operating_expense

        ciq data item 69

    .. py:function:: operating_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 21

    .. py:function:: other_adjustments_to_net_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 259

    .. py:function:: other_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2014

    .. py:function:: other_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1055

    .. py:function:: other_current_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_current_assets

        ciq data item 1029

    .. py:function:: other_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_current_liability

        ciq data item 1057

    .. py:function:: other_current_liability(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1057

    .. py:function:: other_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1028

    .. py:function:: other_financing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2050

    .. py:function:: other_intangibles(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1040

    .. py:function:: other_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2051

    .. py:function:: other_long_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1060

    .. py:function:: other_long_term_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_assets

        ciq data item 1034

    .. py:function:: other_long_term_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_non_current_liabilities

        ciq data item 1062

    .. py:function:: other_non_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_long_term_assets

        ciq data item 1060

    .. py:function:: other_non_current_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_assets

        ciq data item 1034

    .. py:function:: other_non_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1062

    .. py:function:: other_non_operating_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 85

    .. py:function:: other_operating_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2047

    .. py:function:: other_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 260

    .. py:function:: other_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_other

        ciq data item 1065

    .. py:function:: other_preferred_stock_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 281

    .. py:function:: other_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1206

    .. py:function:: other_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 90

    .. py:function:: other_short_term_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_current_assets

        ciq data item 1029

    .. py:function:: other_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 87

    .. py:function:: pension_and_other_post_retirement_benefit(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1213

    .. py:function:: ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: pre_opening_costs(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 96

    .. py:function:: pre_opening_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for pre_opening_costs

        ciq data item 96

    .. py:function:: preferred_dividends_and_other_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 97

    .. py:function:: preferred_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2116

    .. py:function:: preferred_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_preferred_equity

        ciq data item 1005

    .. py:function:: preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_preferred_equity

        ciq data item 1005

    .. py:function:: preferred_stock_additional_paid_in_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1085

    .. py:function:: preferred_stock_convertible(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1214

    .. py:function:: preferred_stock_dividend(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 280

    .. py:function:: preferred_stock_equity_adjustment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1215

    .. py:function:: preferred_stock_non_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1216

    .. py:function:: preferred_stock_other(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1065

    .. py:function:: preferred_stock_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1217

    .. py:function:: premium_on_redemption_of_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 279

    .. py:function:: prepaid_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1212

    .. py:function:: prepaid_expenses(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for prepaid_expense

        ciq data item 1212

    .. py:attribute:: primary_security

        Return the primary security item for the Company object

        :return: a Security object of the primary security of company_id
        :rtype: Security


    .. py:function:: property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: provision_for_bad_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for provision_for_bad_debts

        ciq data item 95

    .. py:function:: provision_for_bad_debts(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 95

    .. py:function:: provision_for_credit_losses(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2112

    .. py:function:: quick_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4121

    .. py:function:: r_and_d_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: r_and_d_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_redeemable

        ciq data item 1217

    .. py:function:: regular_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for revenue

        ciq data item 112

    .. py:function:: relationships(self, relationship_type: kfinance.constants.BusinessRelationshipType) -> 'BusinessRelationships'

        Returns a BusinessRelationships object that includes the current and previous Companies associated with company_id and filtered by relationship_type. The function calls fetch_companies_from_business_relationship.

        :param relationship_type: The type of relationship to filter by. Valid relationship types are defined in the BusinessRelationshipType class.
        :type relationship_type: BusinessRelationshipType
        :return: A BusinessRelationships object containing a tuple of Companies objects that lists current and previous company IDs that have the specified relationship with the given company_id.
        :rtype: BusinessRelationships


    .. py:function:: repurchase_of_common_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2164

    .. py:function:: repurchase_of_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2172

    .. py:function:: research_and_development_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: research_and_development_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 100

    .. py:function:: restricted_cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1104

    .. py:function:: restructuring_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 98

    .. py:function:: retained_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1222

    .. py:function:: revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 112

    .. py:function:: revenue_from_interest_and_investment_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 110

    .. py:function:: revenue_from_sale_of_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 104

    .. py:function:: revenue_from_sale_of_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 106

    .. py:function:: rnd_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: rnd_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: sale_of_intangible_asset(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_intangible_assets

        ciq data item 2029

    .. py:function:: sale_of_intangible_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2029

    .. py:function:: sale_of_intangibles(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_intangible_assets

        ciq data item 2029

    .. py:function:: sale_of_ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_property_plant_and_equipment

        ciq data item 2042

    .. py:function:: sale_of_property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2042

    .. py:function:: sale_of_real_estate(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2040

    .. py:function:: sale_of_real_estate_properties(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_real_estate

        ciq data item 2040

    .. py:function:: sale_of_real_properties(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_real_estate

        ciq data item 2040

    .. py:function:: sale_proceeds_from_rental_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 42411

    .. py:attribute:: securities

        Return the security items for the Company object

        :return: a Securities object containing the list of securities of company_id
        :rtype: Securities


    .. py:function:: selling_general_and_admin(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: selling_general_and_admin_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: selling_general_and_admin_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 102

    .. py:function:: sg_and_a(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: sga(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: shareholders_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_equity

        ciq data item 1275

    .. py:function:: short_term_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for accounts_receivable

        ciq data item 1021

    .. py:function:: short_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_assets

        ciq data item 1008

    .. py:function:: short_term_borrowing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_borrowings

        ciq data item 1046

    .. py:function:: short_term_borrowings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1046

    .. py:function:: short_term_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2043

    .. py:function:: short_term_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2044

    .. py:function:: short_term_deferred_tax_asset(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for deferred_tax_asset_current_portion

        ciq data item 1117

    .. py:function:: short_term_finance_division_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_short_term

        ciq data item 1032

    .. py:function:: short_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1069

    .. py:function:: short_term_loans_and_leases_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_short_term

        ciq data item 1032

    .. py:function:: short_term_notes_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for notes_receivable

        ciq data item 1048

    .. py:function:: short_term_other_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_receivables

        ciq data item 1206

    .. py:function:: short_term_total_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: short_term_total_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: special_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2041

    .. py:function:: statement(self, statement_type: str, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        Get the company's financial statement

    .. py:function:: stock_based_compensation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2127

    .. py:attribute:: strategic_alliance

        Returns the associated company's current and previous strategic_alliances

    .. py:attribute:: supplier

        Returns the associated company's current and previous suppliers

    .. py:function:: tax_benefit_from_stock_options(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2135

    .. py:function:: tax_rate(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for effective_tax_rate

        ciq data item 4376

    .. py:attribute:: tenant

        Returns the associated company's current and previous tenants

    .. py:function:: total_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1007

    .. py:function:: total_cash_and_short_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1002

    .. py:function:: total_common_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1006

    .. py:function:: total_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1008

    .. py:function:: total_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1009

    .. py:function:: total_current_portion_of_long_term_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_long_term_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_lt_debt_and_cap_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_non_current_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_non_current_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_d_and_a(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_depreciation_and_amortization

        ciq data item 2

    .. py:function:: total_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4173

    .. py:function:: total_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2161

    .. py:function:: total_debt_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: total_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2166

    .. py:function:: total_debt_to_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 43907

    .. py:function:: total_debt_to_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: total_debt_to_equity_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4034

    .. py:function:: total_debt_to_total_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: total_depreciation_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2

    .. py:function:: total_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2022

    .. py:function:: total_dna(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_depreciation_and_amortization

        ciq data item 2

    .. py:function:: total_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1275

    .. py:function:: total_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1276

    .. py:function:: total_liabilities_and_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1013

    .. py:function:: total_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 373

    .. py:function:: total_other_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2177

    .. py:function:: total_other_non_cash_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2179

    .. py:function:: total_other_non_operating_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 371

    .. py:function:: total_other_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 380

    .. py:function:: total_other_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 357

    .. py:function:: total_other_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 374

    .. py:function:: total_preferred_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1005

    .. py:function:: total_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_preferred_equity

        ciq data item 1005

    .. py:function:: total_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: total_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1001

    .. py:function:: total_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 28

    .. py:function:: total_selling_general_and_admin(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_selling_general_and_admin_expense

        ciq data item 23

    .. py:function:: total_selling_general_and_admin_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_selling_general_and_admin_expense

        ciq data item 23

    .. py:function:: total_selling_general_and_admin_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 23

    .. py:function:: total_sga(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_selling_general_and_admin_expense

        ciq data item 23

    .. py:function:: total_shareholders_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_equity

        ciq data item 1275

    .. py:function:: total_short_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_assets

        ciq data item 1008

    .. py:function:: total_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 19

    .. py:function:: trading_asset_securities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1244

    .. py:attribute:: transfer_agent

        Returns the associated company's current and previous transfer_agents

    .. py:attribute:: transfer_agent_client

        Returns the associated company's current and previous transfer_agent_clients

    .. py:function:: treasury_convertible_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_convertible

        ciq data item 1249

    .. py:function:: treasury_non_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_non_redeemable

        ciq data item 1250

    .. py:function:: treasury_preferred_stock_convertible(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_convertible

        ciq data item 1249

    .. py:function:: treasury_preferred_stock_non_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_non_redeemable

        ciq data item 1250

    .. py:function:: treasury_preferred_stock_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_redeemable

        ciq data item 1251

    .. py:function:: treasury_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_redeemable

        ciq data item 1251

    .. py:function:: treasury_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1248

    .. py:function:: treasury_stock_convertible_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_convertible

        ciq data item 1249

    .. py:function:: treasury_stock_non_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_non_redeemable

        ciq data item 1250

    .. py:function:: treasury_stock_preferred_stock_convertible(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1249

    .. py:function:: treasury_stock_preferred_stock_non_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1250

    .. py:function:: treasury_stock_preferred_stock_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1251

    .. py:function:: treasury_stock_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_redeemable

        ciq data item 1251

    .. py:function:: unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_unusual_items

        ciq data item 19

    .. py:function:: validate_inputs(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> None

        Test the time inputs for validity.

    .. py:attribute:: vendor

        Returns the associated company's current and previous vendors

    .. py:function:: weighted_average_basic_shares_outstanding(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3217

    .. py:function:: weighted_average_diluted_shares_outstanding(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 342

    .. py:function:: working_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4165

.. py:class:: Securities

    Base class for representing a set of Securities

    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', security_ids: 'Iterable[int]') -> 'None'

        Initialize the Securities

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param security_ids: An iterable of S&P CIQ Security ids
        :type security_ids: Iterable[int]


.. py:class:: Security

    Security class

    :param kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param security_id: The S&P CIQ security id
    :type security_id: int


    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', security_id: 'int')

        Initialize the Security object.

        :param KFinanceApiClient kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param int security_id: The CIQ security id
        :type security_id: int


    .. py:function:: __str__(self) -> 'str'

        String representation for the security object

    .. py:attribute:: cusip

        Get the CUSIP for the object

        :return: The CUSIP
        :rtype: str


    .. py:attribute:: isin

        Get the ISIN for the object

        :return: The ISIN
        :rtype: str


    .. py:attribute:: primary_trading_item

        Return the primary trading item for the Security object

        :return: a TradingItem object of the primary trading item of security_id
        :rtype: TradingItem


    .. py:attribute:: trading_items

        Return the trading items for the Security object

        :return: a TradingItems object containing the list of trading items of security_id
        :rtype: TradingItems


.. py:class:: Ticker

    Base Ticker class for accessing data on company

    :param kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param exchange_code: The exchange code identifying which exchange the ticker is on
    :type exchange_code: str, optional


    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', identifier: 'Optional[str]' = None, exchange_code: 'Optional[str]' = None, company_id: 'Optional[int]' = None, security_id: 'Optional[int]' = None, trading_item_id: 'Optional[int]' = None) -> 'None'

        Initialize the Ticker object. [identifier] can be a ticker, ISIN, or CUSIP. Identifier is prioritized over identification triple (company_id, security_id, & trading_item_id)

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param identifier: The ticker symbol, ISIN, or CUSIP, default None
        :type identifier: str, optional
        :param exchange_code: The exchange code identifying which exchange the ticker is on. It is only needed if symbol is passed in and default None
        :type exchange_code: str, optional
        :param company_id: The S&P Global CIQ Company Id, defaults None
        :type company_id: int, optional
        :param security_id: The S&P Global CIQ Security Id, default None
        :type security_id: int, optional
        :param trading_item_id: The S&P Global CIQ Trading Item Id, default None
        :type trading_item_id: int, optional


    .. py:function:: __str__(self) -> 'str'

        String representation for the ticker object

    .. py:function:: accounts_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1018

    .. py:function:: accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1021

    .. py:function:: accrued_expenses(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1016

    .. py:function:: accumulated_depreciation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1075

    .. py:function:: additional_paid_in_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1084

    .. py:function:: additional_paid_in_capital_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_additional_paid_in_capital

        ciq data item 1085

    .. py:function:: adjustments_to_cash_flow_net_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 21523

    .. py:function:: amortization_of_goodwill_and_intangibles(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 31

    .. py:function:: asset_writedown(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 32

    .. py:function:: assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_assets

        ciq data item 1007

    .. py:function:: balance_sheet(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated balance sheet

    .. py:function:: basic_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps

        ciq data item 9

    .. py:function:: basic_earning_per_share_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_excluding_extra_items

        ciq data item 3064

    .. py:function:: basic_earning_per_share_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_from_accounting_change

        ciq data item 145

    .. py:function:: basic_earning_per_share_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_from_accounting_change_and_extraordinary_items

        ciq data item 45

    .. py:function:: basic_earning_per_share_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps_from_extraordinary_items

        ciq data item 146

    .. py:function:: basic_earning_per_share_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps

        ciq data item 9

    .. py:function:: basic_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 9

    .. py:function:: basic_eps_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3064

    .. py:function:: basic_eps_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 145

    .. py:function:: basic_eps_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 45

    .. py:function:: basic_eps_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 146

    .. py:function:: basic_eps_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for basic_eps

        ciq data item 9

    .. py:attribute:: borrower

        Returns the associated company's current and previous borrowers

    .. py:function:: capex(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_expenditure

        ciq data item 2021

    .. py:function:: capital_expenditure(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2021

    .. py:function:: capital_expenditures(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_expenditure

        ciq data item 2021

    .. py:function:: capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1183

    .. py:function:: capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_leases

        ciq data item 1183

    .. py:function:: cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_and_equivalents

        ciq data item 1096

    .. py:function:: cash_acquisitions(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2057

    .. py:function:: cash_and_cash_equivalents(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_and_equivalents

        ciq data item 1096

    .. py:function:: cash_and_equivalents(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1096

    .. py:function:: cash_and_short_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_cash_and_short_term_investments

        ciq data item 1002

    .. py:function:: cash_flow(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated cash flow statement

    .. py:function:: cash_flow_from_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_operations

        ciq data item 2006

    .. py:function:: cash_from_discontinued_operation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_cash_from_discontinued_operation

        ciq data item 2081

    .. py:function:: cash_from_financing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2004

    .. py:function:: cash_from_financing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_financing

        ciq data item 2004

    .. py:function:: cash_from_investing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2005

    .. py:function:: cash_from_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_investing

        ciq data item 2005

    .. py:function:: cash_from_operating_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_operations

        ciq data item 2006

    .. py:function:: cash_from_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2006

    .. py:function:: cashflow(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated cash flow statement

    .. py:function:: cashflow_from_financing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_financing

        ciq data item 2004

    .. py:function:: cashflow_from_financing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_financing

        ciq data item 2004

    .. py:function:: cashflow_from_investing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_investing

        ciq data item 2005

    .. py:function:: cashflow_from_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cash_from_investing

        ciq data item 2005

    .. py:function:: change_in_accounts_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2017

    .. py:function:: change_in_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2018

    .. py:function:: change_in_cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_change_in_cash

        ciq data item 2093

    .. py:function:: change_in_deferred_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2084

    .. py:function:: change_in_income_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2101

    .. py:function:: change_in_inventories(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2099

    .. py:function:: change_in_net_operating_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2010

    .. py:function:: change_in_net_working_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4421

    .. py:function:: change_in_other_net_operating_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2045

    .. py:function:: change_in_trading_asset_securities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2134

    .. py:function:: change_in_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2139

    .. py:attribute:: client_services

        Returns the associated company's current and previous client_servicess

    .. py:function:: cogs(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cost_of_goods_sold

        ciq data item 34

    .. py:function:: common_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2074

    .. py:function:: common_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_common_equity

        ciq data item 1006

    .. py:function:: common_shares_outstanding(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1100

    .. py:function:: common_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1103

    .. py:attribute:: company

        Set and return the company for the object

        :return: The company returned as Company object
        :rtype: Company


    .. py:attribute:: company_id

        Get the company id for the object

        :return: the CIQ company id
        :rtype: int


    .. py:function:: continued_operations_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for earnings_from_continued_operations

        ciq data item 7

    .. py:function:: convertible_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_convertible

        ciq data item 1214

    .. py:function:: cor(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for cost_of_revenue

        ciq data item 1

    .. py:function:: cost_of_goods_sold(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 34

    .. py:function:: cost_of_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1

    .. py:attribute:: creditor

        Returns the associated company's current and previous creditors

    .. py:function:: currency_exchange_gains(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 38

    .. py:function:: current_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for accounts_receivable

        ciq data item 1021

    .. py:function:: current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_assets

        ciq data item 1008

    .. py:function:: current_borrowing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_borrowings

        ciq data item 1046

    .. py:function:: current_borrowings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_borrowings

        ciq data item 1046

    .. py:function:: current_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_debt_issued

        ciq data item 2043

    .. py:function:: current_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_debt_repaid

        ciq data item 2044

    .. py:function:: current_deferred_tax_asset(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for deferred_tax_asset_current_portion

        ciq data item 1117

    .. py:function:: current_deferred_tax_liability(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1119

    .. py:function:: current_income_taxes_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1094

    .. py:function:: current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_liabilities

        ciq data item 1009

    .. py:function:: current_notes_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for notes_receivable

        ciq data item 1048

    .. py:function:: current_other_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_receivables

        ciq data item 1206

    .. py:function:: current_portion_of_cap_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_capital_leases

        ciq data item 1090

    .. py:function:: current_portion_of_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1090

    .. py:function:: current_portion_of_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_capital_leases

        ciq data item 1090

    .. py:function:: current_portion_of_income_taxes_payable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_income_taxes_payable

        ciq data item 1094

    .. py:function:: current_portion_of_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_capital_leases

        ciq data item 1090

    .. py:function:: current_portion_of_long_term_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1297

    .. py:function:: current_portion_of_long_term_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1279

    .. py:function:: current_portion_of_long_term_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_lt_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt

        ciq data item 1297

    .. py:function:: current_portion_of_lt_debt_and_cap_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_non_current_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt

        ciq data item 1297

    .. py:function:: current_portion_of_non_current_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_non_current_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: current_portion_of_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_unearned_revenue

        ciq data item 1074

    .. py:function:: current_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4030

    .. py:function:: current_total_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: current_total_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: current_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1074

    .. py:attribute:: cusip

        Get the CUSIP for the object

        :return: The CUSIP
        :rtype: str


    .. py:attribute:: customer

        Returns the associated company's current and previous customers

    .. py:function:: d_and_a(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for depreciation_and_amortization

        ciq data item 41

    .. py:function:: debt_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: deferred_tax_asset_current_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1117

    .. py:function:: depreciation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2143

    .. py:function:: depreciation_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 41

    .. py:function:: depreciation_of_rental_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 42409

    .. py:function:: diluted_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps

        ciq data item 8

    .. py:function:: diluted_earning_per_share_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_excluding_extra_items

        ciq data item 142

    .. py:function:: diluted_earning_per_share_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_accounting_change

        ciq data item 141

    .. py:function:: diluted_earning_per_share_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_accounting_change_and_extraordinary_items

        ciq data item 44

    .. py:function:: diluted_earning_per_share_from_discontinued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_discontinued_operations

        ciq data item 143

    .. py:function:: diluted_earning_per_share_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps_from_extraordinary_items

        ciq data item 144

    .. py:function:: diluted_earning_per_share_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps

        ciq data item 8

    .. py:function:: diluted_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 8

    .. py:function:: diluted_eps_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 142

    .. py:function:: diluted_eps_from_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 141

    .. py:function:: diluted_eps_from_accounting_change_and_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 44

    .. py:function:: diluted_eps_from_discontinued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 143

    .. py:function:: diluted_eps_from_extraordinary_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 144

    .. py:function:: diluted_eps_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for diluted_eps

        ciq data item 8

    .. py:function:: discontinued_operations_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for earnings_from_discontinued_operations

        ciq data item 40

    .. py:function:: distributable_cash_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 23317

    .. py:attribute:: distributor

        Returns the associated company's current and previous distributors

    .. py:function:: divestitures(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2077

    .. py:function:: dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_dividends_paid

        ciq data item 2022

    .. py:function:: dividends_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3058

    .. py:function:: dna(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for depreciation_and_amortization

        ciq data item 41

    .. py:function:: earnings_before_interest_and_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebit

        ciq data item 400

    .. py:function:: earnings_before_interest_taxes_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebita

        ciq data item 100689

    .. py:function:: earnings_before_interest_taxes_depreciation_amortization_and_rental_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebitdar

        ciq data item 21674

    .. py:function:: earnings_before_interest_taxes_depreciation_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebitda

        ciq data item 4051

    .. py:function:: earnings_before_taxes_excluding_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebt_excluding_unusual_items

        ciq data item 4

    .. py:function:: earnings_before_taxes_including_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for ebt_including_unusual_items

        ciq data item 139

    .. py:attribute:: earnings_call_datetimes

        Get the datetimes of the companies earnings calls

        :return: a list of datetimes for the companies earnings calls
        :rtype: list[datetime]


    .. py:function:: earnings_from_continued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 7

    .. py:function:: earnings_from_discontinued_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 40

    .. py:function:: ebit(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 400

    .. py:function:: ebita(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 100689

    .. py:function:: ebitda(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4051

    .. py:function:: ebitdar(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 21674

    .. py:function:: ebt_excluding_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4

    .. py:function:: ebt_including_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 139

    .. py:function:: effective_tax_rate(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4376

    .. py:function:: equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_equity

        ciq data item 1275

    .. py:function:: equity_adjustment_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_equity_adjustment

        ciq data item 1215

    .. py:function:: exploration_and_drilling_costs(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 49

    .. py:function:: exploration_and_drilling_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for exploration_and_drilling_costs

        ciq data item 49

    .. py:function:: extraordinary_item_and_accounting_change(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 42

    .. py:function:: fees_and_other_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 168

    .. py:function:: ffo(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for funds_from_operations

        ciq data item 3074

    .. py:function:: finance_division_debt_current_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1030

    .. py:function:: finance_division_debt_long_term_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_debt_non_current_portion

        ciq data item 1035

    .. py:function:: finance_division_debt_non_current_portion(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1035

    .. py:function:: finance_division_interest_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 50

    .. py:function:: finance_division_loans_and_leases_long_term(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1033

    .. py:function:: finance_division_loans_and_leases_short_term(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1032

    .. py:function:: finance_division_long_term_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_debt_non_current_portion

        ciq data item 1035

    .. py:function:: finance_division_long_term_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_long_term

        ciq data item 1033

    .. py:function:: finance_division_non_current_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_debt_non_current_portion

        ciq data item 1035

    .. py:function:: finance_division_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 51

    .. py:function:: finance_division_other_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1029

    .. py:function:: finance_division_other_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1031

    .. py:function:: finance_division_other_long_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_assets

        ciq data item 1034

    .. py:function:: finance_division_other_long_term_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_liabilities

        ciq data item 1036

    .. py:function:: finance_division_other_non_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1034

    .. py:function:: finance_division_other_non_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1036

    .. py:function:: finance_division_other_short_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_current_assets

        ciq data item 1029

    .. py:function:: finance_division_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 52

    .. py:function:: finance_division_short_term_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_short_term

        ciq data item 1032

    .. py:function:: foreign_exchange_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for foreign_exchange_rate_adjustments

        ciq data item 2144

    .. py:function:: foreign_exchange_rate_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2144

    .. py:attribute:: franchisee

        Returns the associated company's current and previous franchisees

    .. py:attribute:: franchisor

        Returns the associated company's current and previous franchisors

    .. py:function:: funds_from_operations(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3074

    .. py:function:: fx_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for foreign_exchange_rate_adjustments

        ciq data item 2144

    .. py:function:: gain_from_sale_of_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 62

    .. py:function:: gain_from_sale_of_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 56

    .. py:function:: goodwill(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1171

    .. py:function:: gppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for gross_property_plant_and_equipment

        ciq data item 1169

    .. py:function:: gross_ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for gross_property_plant_and_equipment

        ciq data item 1169

    .. py:function:: gross_profit(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 10

    .. py:function:: gross_property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1169

    .. py:function:: history(self, periodicity: 'str' = 'day', adjusted: 'bool' = True, start_date: 'Optional[str]' = None, end_date: 'Optional[str]' = None) -> 'pd.DataFrame'

        Retrieves the historical price data for a given asset over a specified date range.

        :param periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :type periodicity: str
        :param adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :type adjusted: bool, optional
        :param start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: A pd.DataFrame containing historical price data with columns corresponding to the specified periodicity, with Date as the index, and columns "open", "high", "low", "close", "volume" in type decimal. The Date index is a string that depends on the periodicity. If periodicity="day", the Date index is the day in format "YYYY-MM-DD", eg "2024-05-13" If periodicity="week", the Date index is the week number of the year in format "YYYY Week ##", eg "2024 Week 2" If periodicity="month", the Date index is the month name of the year in format "<Month> YYYY", eg "January 2024". If periodicity="year", the Date index is the year in format "YYYY", eg "2024".
        :rtype: pd.DataFrame


    .. py:attribute:: history_metadata

        Get information about exchange and quotation

        :return: A dict containing data about the currency, symbol, exchange, type of instrument, and the first trading date
        :rtype: HistoryMetadata


    .. py:function:: impairment_o_and_g(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for impairment_of_oil_gas_and_mineral_properties

        ciq data item 71

    .. py:function:: impairment_of_goodwill(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 209

    .. py:function:: impairment_of_oil_and_gas(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for impairment_of_oil_gas_and_mineral_properties

        ciq data item 71

    .. py:function:: impairment_of_oil_gas_and_mineral_properties(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 71

    .. py:function:: in_process_r_and_d_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_r_and_d_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_research_and_development_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_research_and_development_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 72

    .. py:function:: in_process_rnd_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: in_process_rnd_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for in_process_research_and_development_expense

        ciq data item 72

    .. py:function:: income_from_affiliates(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 47

    .. py:function:: income_statement(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated income statement

    .. py:function:: income_stmt(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        The templated income statement

    .. py:function:: income_tax(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for income_tax_expense

        ciq data item 75

    .. py:function:: income_tax_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 75

    .. py:function:: income_taxes(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for income_tax_expense

        ciq data item 75

    .. py:attribute:: info

        Get the company info for the ticker

        :return: a dict with containing: name, status, type, simple industry, number of employees, founding date, webpage, address, city, zip code, state, country, & iso_country
        :rtype: dict


    .. py:function:: insurance_division_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 69

    .. py:function:: insurance_division_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 70

    .. py:function:: insurance_settlements(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 73

    .. py:function:: interest_and_investment_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 65

    .. py:function:: interest_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 82

    .. py:function:: interest_expense_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_interest_expense

        ciq data item 50

    .. py:function:: inventories(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for inventory

        ciq data item 1043

    .. py:function:: inventory(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1043

    .. py:attribute:: investor_relations_client

        Returns the associated company's current and previous investor_relations_clients

    .. py:attribute:: investor_relations_firm

        Returns the associated company's current and previous investor_relations_firms

    .. py:attribute:: isin

        Get the ISIN for the object

        :return: The ISIN
        :rtype: str


    .. py:function:: issuance_of_common_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2169

    .. py:function:: issuance_of_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2181

    .. py:attribute:: landlord

        Returns the associated company's current and previous landlords

    .. py:function:: legal_settlements(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 77

    .. py:attribute:: lessee

        Returns the associated company's current and previous lessees

    .. py:attribute:: lessor

        Returns the associated company's current and previous lessors

    .. py:function:: liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_liabilities

        ciq data item 1276

    .. py:function:: liabilities_and_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_liabilities_and_equity

        ciq data item 1013

    .. py:attribute:: licensee

        Returns the associated company's current and previous licensees

    .. py:attribute:: licensor

        Returns the associated company's current and previous licensors

    .. py:function:: line_item(self, line_item: str, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        Get a DataFrame of a financial line item according to the date ranges.

    .. py:function:: loans_held_for_sale(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1185

    .. py:function:: loans_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_loans_receivable

        ciq data item 1050

    .. py:function:: long_term_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1088

    .. py:function:: long_term_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1049

    .. py:function:: long_term_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2034

    .. py:function:: long_term_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2036

    .. py:function:: long_term_deferred_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1025

    .. py:function:: long_term_deferred_tax_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1026

    .. py:function:: long_term_finance_division_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_long_term

        ciq data item 1033

    .. py:function:: long_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1054

    .. py:function:: long_term_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for capital_leases

        ciq data item 1183

    .. py:function:: long_term_loans_and_leases_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_long_term

        ciq data item 1033

    .. py:function:: long_term_loans_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1050

    .. py:function:: long_term_other_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_long_term_assets

        ciq data item 1060

    .. py:function:: long_term_other_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_non_current_liabilities

        ciq data item 1062

    .. py:function:: long_term_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for non_current_unearned_revenue

        ciq data item 1256

    .. py:function:: loss_on_equity_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2086

    .. py:function:: merger_and_restructuring_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 363

    .. py:function:: merger_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 80

    .. py:function:: minority_interest_in_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 83

    .. py:function:: misc_cash_flow_adj(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for miscellaneous_cash_flow_adjustments

        ciq data item 2149

    .. py:function:: miscellaneous_cash_flow_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2149

    .. py:function:: net_cash_from_discontinued_operation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2081

    .. py:function:: net_cash_from_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2027

    .. py:function:: net_change_in_cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2093

    .. py:function:: net_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4364

    .. py:function:: net_decrease_in_investment_loans_originated_and_sold(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2032

    .. py:function:: net_decrease_in_loans_originated_and_sold(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2033

    .. py:function:: net_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 15

    .. py:function:: net_income_allocable_to_general_partner(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 249

    .. py:function:: net_income_to_common_shareholders_excluding_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 379

    .. py:function:: net_income_to_common_shareholders_including_extra_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 16

    .. py:function:: net_income_to_company(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 41571

    .. py:function:: net_income_to_minority_interest(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for minority_interest_in_earnings

        ciq data item 83

    .. py:function:: net_interest_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 368

    .. py:function:: net_ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: net_property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1004

    .. py:function:: net_working_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1311

    .. py:function:: non_current_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_accounts_receivable

        ciq data item 1088

    .. py:function:: non_current_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_debt

        ciq data item 1049

    .. py:function:: non_current_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_debt_issued

        ciq data item 2034

    .. py:function:: non_current_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_debt_repaid

        ciq data item 2036

    .. py:function:: non_current_deferred_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_deferred_charges

        ciq data item 1025

    .. py:function:: non_current_deferred_tax_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_deferred_tax_assets

        ciq data item 1026

    .. py:function:: non_current_deferred_tax_liability(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1027

    .. py:function:: non_current_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_investments

        ciq data item 1054

    .. py:function:: non_current_loans_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for long_term_loans_receivable

        ciq data item 1050

    .. py:function:: non_current_other_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_long_term_assets

        ciq data item 1060

    .. py:function:: non_current_other_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_non_current_liabilities

        ciq data item 1062

    .. py:function:: non_current_unearned_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1256

    .. py:function:: non_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_non_redeemable

        ciq data item 1216

    .. py:function:: normal_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for revenue

        ciq data item 112

    .. py:function:: normalized_basic_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for normalized_basic_eps

        ciq data item 4379

    .. py:function:: normalized_basic_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4379

    .. py:function:: normalized_diluted_earning_per_share(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for normalized_diluted_eps

        ciq data item 4380

    .. py:function:: normalized_diluted_eps(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4380

    .. py:function:: notes_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1048

    .. py:function:: nppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_operating_expense

        ciq data item 373

    .. py:function:: operating_expense_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_operating_expense

        ciq data item 51

    .. py:function:: operating_expense_insurance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for insurance_division_operating_expense

        ciq data item 69

    .. py:function:: operating_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 21

    .. py:function:: other_adjustments_to_net_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 259

    .. py:function:: other_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2014

    .. py:function:: other_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1055

    .. py:function:: other_current_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_current_assets

        ciq data item 1029

    .. py:function:: other_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_current_liability

        ciq data item 1057

    .. py:function:: other_current_liability(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1057

    .. py:function:: other_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1028

    .. py:function:: other_financing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2050

    .. py:function:: other_intangibles(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1040

    .. py:function:: other_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2051

    .. py:function:: other_long_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1060

    .. py:function:: other_long_term_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_assets

        ciq data item 1034

    .. py:function:: other_long_term_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_non_current_liabilities

        ciq data item 1062

    .. py:function:: other_non_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_long_term_assets

        ciq data item 1060

    .. py:function:: other_non_current_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_non_current_assets

        ciq data item 1034

    .. py:function:: other_non_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1062

    .. py:function:: other_non_operating_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 85

    .. py:function:: other_operating_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2047

    .. py:function:: other_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 260

    .. py:function:: other_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_other

        ciq data item 1065

    .. py:function:: other_preferred_stock_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 281

    .. py:function:: other_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1206

    .. py:function:: other_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 90

    .. py:function:: other_short_term_assets_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_other_current_assets

        ciq data item 1029

    .. py:function:: other_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 87

    .. py:function:: pension_and_other_post_retirement_benefit(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1213

    .. py:function:: ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: pre_opening_costs(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 96

    .. py:function:: pre_opening_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for pre_opening_costs

        ciq data item 96

    .. py:function:: preferred_dividends_and_other_adjustments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 97

    .. py:function:: preferred_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2116

    .. py:function:: preferred_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_preferred_equity

        ciq data item 1005

    .. py:function:: preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_preferred_equity

        ciq data item 1005

    .. py:function:: preferred_stock_additional_paid_in_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1085

    .. py:function:: preferred_stock_convertible(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1214

    .. py:function:: preferred_stock_dividend(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 280

    .. py:function:: preferred_stock_equity_adjustment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1215

    .. py:function:: preferred_stock_non_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1216

    .. py:function:: preferred_stock_other(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1065

    .. py:function:: preferred_stock_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1217

    .. py:function:: premium_on_redemption_of_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 279

    .. py:function:: prepaid_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1212

    .. py:function:: prepaid_expenses(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for prepaid_expense

        ciq data item 1212

    .. py:function:: price_chart(self, periodicity: 'str' = 'day', adjusted: 'bool' = True, start_date: 'Optional[str]' = None, end_date: 'Optional[str]' = None) -> 'Image'

        Get the price chart.

        :param periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :type periodicity: str
        :param adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :type adjusted: bool, optional
        :param start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type start_date: str, optional
        :param end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :type end_date: str, optional
        :return: An image showing the price chart of the trading item
        :rtype: Image


    .. py:attribute:: primary_security

        Set and return the primary security for the object

        :return: The primary security as a Security object
        :rtype: Security


    .. py:attribute:: primary_trading_item

        Set and return the trading item for the object

        :return: The trading item returned as TradingItem object
        :rtype: TradingItem


    .. py:function:: property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for net_property_plant_and_equipment

        ciq data item 1004

    .. py:function:: provision_for_bad_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for provision_for_bad_debts

        ciq data item 95

    .. py:function:: provision_for_bad_debts(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 95

    .. py:function:: provision_for_credit_losses(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2112

    .. py:function:: quick_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4121

    .. py:function:: r_and_d_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: r_and_d_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for preferred_stock_redeemable

        ciq data item 1217

    .. py:function:: regular_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for revenue

        ciq data item 112

    .. py:function:: relationships(self, relationship_type: kfinance.constants.BusinessRelationshipType) -> 'BusinessRelationships'

        Returns a BusinessRelationships object that includes the current and previous Companies associated with company_id and filtered by relationship_type. The function calls fetch_companies_from_business_relationship.

        :param relationship_type: The type of relationship to filter by. Valid relationship types are defined in the BusinessRelationshipType class.
        :type relationship_type: BusinessRelationshipType
        :return: A BusinessRelationships object containing a tuple of Companies objects that lists current and previous company IDs that have the specified relationship with the given company_id.
        :rtype: BusinessRelationships


    .. py:function:: repurchase_of_common_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2164

    .. py:function:: repurchase_of_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2172

    .. py:function:: research_and_development_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: research_and_development_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 100

    .. py:function:: restricted_cash(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1104

    .. py:function:: restructuring_charges(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 98

    .. py:function:: retained_earnings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1222

    .. py:function:: revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 112

    .. py:function:: revenue_from_interest_and_investment_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 110

    .. py:function:: revenue_from_sale_of_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 104

    .. py:function:: revenue_from_sale_of_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 106

    .. py:function:: rnd_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: rnd_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for research_and_development_expense

        ciq data item 100

    .. py:function:: sale_of_intangible_asset(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_intangible_assets

        ciq data item 2029

    .. py:function:: sale_of_intangible_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2029

    .. py:function:: sale_of_intangibles(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_intangible_assets

        ciq data item 2029

    .. py:function:: sale_of_ppe(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_property_plant_and_equipment

        ciq data item 2042

    .. py:function:: sale_of_property_plant_and_equipment(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2042

    .. py:function:: sale_of_real_estate(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2040

    .. py:function:: sale_of_real_estate_properties(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_real_estate

        ciq data item 2040

    .. py:function:: sale_of_real_properties(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for sale_of_real_estate

        ciq data item 2040

    .. py:function:: sale_proceeds_from_rental_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 42411

    .. py:attribute:: security_id

        Get the CIQ security id for the object

        :return: the CIQ security id
        :rtype: int


    .. py:function:: selling_general_and_admin(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: selling_general_and_admin_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: selling_general_and_admin_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 102

    .. py:function:: set_company_id(self) -> 'int'

        Set the company id for the object

        :return: the CIQ company id
        :rtype: int


    .. py:function:: set_identification_triple(self) -> 'None'

        Get & set company_id, security_id, & trading_item_id for ticker with an exchange

    .. py:function:: set_security_id(self) -> 'int'

        Set the security id for the object

        :return: the CIQ security id
        :rtype: int


    .. py:function:: set_trading_item_id(self) -> 'int'

        Set the trading item id for the object

        :return: the CIQ trading item id
        :rtype: int


    .. py:function:: sg_and_a(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: sga(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for selling_general_and_admin_expense

        ciq data item 102

    .. py:function:: shareholders_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_equity

        ciq data item 1275

    .. py:function:: short_term_accounts_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for accounts_receivable

        ciq data item 1021

    .. py:function:: short_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_assets

        ciq data item 1008

    .. py:function:: short_term_borrowing(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for short_term_borrowings

        ciq data item 1046

    .. py:function:: short_term_borrowings(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1046

    .. py:function:: short_term_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2043

    .. py:function:: short_term_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2044

    .. py:function:: short_term_deferred_tax_asset(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for deferred_tax_asset_current_portion

        ciq data item 1117

    .. py:function:: short_term_finance_division_loans_and_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_short_term

        ciq data item 1032

    .. py:function:: short_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1069

    .. py:function:: short_term_loans_and_leases_of_the_finance_division(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for finance_division_loans_and_leases_short_term

        ciq data item 1032

    .. py:function:: short_term_notes_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for notes_receivable

        ciq data item 1048

    .. py:function:: short_term_other_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for other_receivables

        ciq data item 1206

    .. py:function:: short_term_total_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: short_term_total_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: special_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2041

    .. py:function:: statement(self, statement_type: str, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        Get the company's financial statement

    .. py:function:: stock_based_compensation(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2127

    .. py:attribute:: strategic_alliance

        Returns the associated company's current and previous strategic_alliances

    .. py:attribute:: supplier

        Returns the associated company's current and previous suppliers

    .. py:function:: tax_benefit_from_stock_options(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2135

    .. py:function:: tax_rate(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for effective_tax_rate

        ciq data item 4376

    .. py:attribute:: tenant

        Returns the associated company's current and previous tenants

    .. py:attribute:: ticker

        Get the ticker if it isn't available from initialization

    .. py:function:: total_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1007

    .. py:function:: total_cash_and_short_term_investments(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1002

    .. py:function:: total_common_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1006

    .. py:function:: total_current_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1008

    .. py:function:: total_current_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1009

    .. py:function:: total_current_portion_of_long_term_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_long_term_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_lt_debt_and_cap_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_non_current_debt_and_capital_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_current_portion_of_non_current_debt_and_capitalized_leases(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for current_portion_of_long_term_debt_and_capital_leases

        ciq data item 1279

    .. py:function:: total_d_and_a(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_depreciation_and_amortization

        ciq data item 2

    .. py:function:: total_debt(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4173

    .. py:function:: total_debt_issued(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2161

    .. py:function:: total_debt_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: total_debt_repaid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2166

    .. py:function:: total_debt_to_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 43907

    .. py:function:: total_debt_to_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: total_debt_to_equity_ratio(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4034

    .. py:function:: total_debt_to_total_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_debt_to_equity_ratio

        ciq data item 4034

    .. py:function:: total_depreciation_and_amortization(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2

    .. py:function:: total_dividends_paid(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2022

    .. py:function:: total_dna(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_depreciation_and_amortization

        ciq data item 2

    .. py:function:: total_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1275

    .. py:function:: total_liabilities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1276

    .. py:function:: total_liabilities_and_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1013

    .. py:function:: total_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 373

    .. py:function:: total_other_investing_activities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2177

    .. py:function:: total_other_non_cash_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 2179

    .. py:function:: total_other_non_operating_income(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 371

    .. py:function:: total_other_operating_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 380

    .. py:function:: total_other_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 357

    .. py:function:: total_other_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 374

    .. py:function:: total_preferred_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1005

    .. py:function:: total_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_preferred_equity

        ciq data item 1005

    .. py:function:: total_receivable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_receivables

        ciq data item 1001

    .. py:function:: total_receivables(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1001

    .. py:function:: total_revenue(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 28

    .. py:function:: total_selling_general_and_admin(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_selling_general_and_admin_expense

        ciq data item 23

    .. py:function:: total_selling_general_and_admin_cost(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_selling_general_and_admin_expense

        ciq data item 23

    .. py:function:: total_selling_general_and_admin_expense(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 23

    .. py:function:: total_sga(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_selling_general_and_admin_expense

        ciq data item 23

    .. py:function:: total_shareholders_equity(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_equity

        ciq data item 1275

    .. py:function:: total_short_term_assets(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_current_assets

        ciq data item 1008

    .. py:function:: total_unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 19

    .. py:function:: trading_asset_securities(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1244

    .. py:attribute:: trading_item_id

        Get the CIQ trading item id for the object

        :return: the CIQ trading item id
        :rtype: int


    .. py:attribute:: transfer_agent

        Returns the associated company's current and previous transfer_agents

    .. py:attribute:: transfer_agent_client

        Returns the associated company's current and previous transfer_agent_clients

    .. py:function:: treasury_convertible_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_convertible

        ciq data item 1249

    .. py:function:: treasury_non_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_non_redeemable

        ciq data item 1250

    .. py:function:: treasury_preferred_stock_convertible(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_convertible

        ciq data item 1249

    .. py:function:: treasury_preferred_stock_non_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_non_redeemable

        ciq data item 1250

    .. py:function:: treasury_preferred_stock_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_redeemable

        ciq data item 1251

    .. py:function:: treasury_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_redeemable

        ciq data item 1251

    .. py:function:: treasury_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1248

    .. py:function:: treasury_stock_convertible_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_convertible

        ciq data item 1249

    .. py:function:: treasury_stock_non_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_non_redeemable

        ciq data item 1250

    .. py:function:: treasury_stock_preferred_stock_convertible(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1249

    .. py:function:: treasury_stock_preferred_stock_non_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1250

    .. py:function:: treasury_stock_preferred_stock_redeemable(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 1251

    .. py:function:: treasury_stock_redeemable_preferred_stock(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for treasury_stock_preferred_stock_redeemable

        ciq data item 1251

    .. py:function:: unusual_items(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        alias for total_unusual_items

        ciq data item 19

    .. py:function:: validate_inputs(self, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> None

        Test the time inputs for validity.

    .. py:attribute:: vendor

        Returns the associated company's current and previous vendors

    .. py:function:: weighted_average_basic_shares_outstanding(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 3217

    .. py:function:: weighted_average_diluted_shares_outstanding(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 342

    .. py:function:: working_capital(self: Any, period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pandas.core.frame.DataFrame

        ciq data item 4165

.. py:class:: Tickers

    Base TickerSet class for representing a set of Tickers

    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', id_triples: 'Iterable[IdentificationTriple]') -> 'None'

        Initialize the Ticker Set

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param id_triples: An Iterable of IdentificationTriples that will become the ticker objects making up the tickers object
        :type id_triples: Iterable[IdentificationTriple]


    .. py:function:: companies(self) -> 'Companies'

        Build a group of company objects from the group of tickers

        :return: The Companies corresponding to the Tickers
        :rtype: Companies


    .. py:function:: securities(self) -> 'Securities'

        Build a group of security objects from the group of tickers

        :return: The Securities corresponding to the Tickers
        :rtype: Securities


    .. py:function:: trading_items(self) -> 'TradingItems'

        Build a group of trading item objects from the group of ticker

        :return: The TradingItems corresponding to the Tickers
        :rtype: TradingItems


.. py:class:: TradingItem

    Trading Class

    :param kfinance_api_client: The KFinanceApiClient used to fetch data
    :type kfinance_api_client: KFinanceApiClient
    :param trading_item_id: The S&P CIQ Trading Item ID
    :type trading_item_id: int


    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', trading_item_id: 'int')

        Initialize the trading item object

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param trading_item_id: The S&P CIQ Trading Item ID
        :type trading_item_id: int


    .. py:function:: __str__(self) -> 'str'

        String representation for the company object

    .. py:function:: from_ticker(kfinance_api_client: 'KFinanceApiClient', ticker: 'str', exchange_code: 'Optional[str]' = None) -> "'TradingItem'"

        Return TradingItem object from ticker

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param ticker: the ticker symbol
        :type ticker: str
        :param exchange_code: The exchange code identifying which exchange the ticker is on.
        :type exchange_code: str, optional


    .. py:function:: history(self, periodicity: 'str' = 'day', adjusted: 'bool' = True, start_date: 'Optional[str]' = None, end_date: 'Optional[str]' = None) -> 'pd.DataFrame'

        Retrieves the historical price data for a given asset over a specified date range.

        :param str periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :param Optional[bool] adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :param Optional[str] start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :param Optional[str] end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :return: A pd.DataFrame containing historical price data with columns corresponding to the specified periodicity, with Date as the index, and columns "open", "high", "low", "close", "volume" in type decimal. The Date index is a string that depends on the periodicity. If periodicity="day", the Date index is the day in format "YYYY-MM-DD", eg "2024-05-13" If periodicity="week", the Date index is the week number of the year in format "YYYY Week ##", eg "2024 Week 2" If periodicity="month", the Date index is the month name of the year in format "<Month> YYYY", eg "January 2024". If periodicity="year", the Date index is the year in format "YYYY", eg "2024".
        :rtype: pd.DataFrame


    .. py:attribute:: history_metadata

        Get information about exchange and quotation

        :return: A dict containing data about the currency, symbol, exchange, type of instrument, and the first trading date
        :rtype: HistoryMetadata


    .. py:function:: price_chart(self, periodicity: 'str' = 'day', adjusted: 'bool' = True, start_date: 'Optional[str]' = None, end_date: 'Optional[str]' = None) -> 'Image'

        Get the price chart.

        :param str periodicity: Determines the frequency of the historical data returned. Options are "day", "week", "month" and "year". This default to "day"
        :param Optional[bool] adjusted: Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits, it defaults True
        :param Optional[str] start_date: The start date for historical price retrieval in format "YYYY-MM-DD", default to None
        :param Optional[str] end_date: The end date for historical price retrieval in format "YYYY-MM-DD", default to None
        :return: An image showing the price chart of the trading item
        :rtype: Image


    .. py:attribute:: trading_item_id

        Get the trading item id for the object

        :return: the CIQ trading item id
        :rtype: int


.. py:class:: TradingItems

    Base class for representing a set of Trading Items

    .. py:function:: __init__(self, kfinance_api_client: 'KFinanceApiClient', trading_item_ids: 'Iterable[int]') -> 'None'

        Initialize the Trading Items

        :param kfinance_api_client: The KFinanceApiClient used to fetch data
        :type kfinance_api_client: KFinanceApiClient
        :param company_ids: An iterable of S&P CIQ Company ids
        :type company_ids: Iterable[int]
