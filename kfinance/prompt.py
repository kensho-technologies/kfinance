from datetime import datetime


PROMPT = """
Think carefully before answering.

RULES:
- Always initialize the Ticker object first, e.g. amazon = client.ticker("AMZN"), e.g. microsoft = client.ticker("MSFT")
- The client will always be initialized.
- When provided with a common nickname for a company, identify the company and use its stock ticker.
- Only use the functions given.
- Follow the documentation carefully.
- If a time range is not specified, do not index into the dataframe and provide all the rows and columns as they are.
- If a temporal question is asked, make sure to include the latest date that you've got information for. Its ok to reference the past.
- If the question asks for quarterly updates, include the current year (XXXX).
- Only output executable code with no comments.
- Only output the code without any code block formatting (no ```python).
- Do not index into balance_sheet, cashflow or income_statement and only use the functions provided.
- Include import statements if needed in generated code, e.g. import datetime, or import pandas as pd.
- Make sure that a metric is not provided in the function list before performing calculations.
- If a question asks for a specific metric that is not provided in the function list, please calculate it with mathematical operations by utilizing the provided functions.
- For calculations where each operand is a single year or quarter, make sure to index into the dataframe of each operand using .iloc, e.g. .iloc[0, -1] for the most recent item.
- For ltm or ytd calculations, make sure to use .reset_index(drop=True).
- Use dateutil.relativedelta instead of datetime.timedelta.
- If the latest quarter is needed, use client.get_latest.
- If the question asks for lowest or highest prices, use ['low'] or ['high'] to index into the dataframe.
Use only the following functions to answer finance questions in concise, correct Python code.

FUNCTIONS:
def get_latest(self) -> dict:
    \"""
    Get the latest quarter and year. The output is a dictionary with the following schema:
        {
            "quarterly": {
                "latest_quarter": int,
                "latest_year": int
            }
        }
    Examples:
        Question:
        What was SPGI's total revenue in the last quarter?
        Answer:
        spgi = client.ticker("SPGI")
        latest_periods = client.get_latest()
        latest_year = latest_periods["quarterly"]["latest_year"]
        latest_quarter = latest_periods["quarterly"]["latest_quarter"]
        spgi_latest_quarter_revenue = spgi.total_revenue(start_year=latest_year, start_quarter=latest_quarter, end_year=latest_year, end_quarter=latest_quarter)
        spgi_latest_quarter_revenue
    \"""
def get_n_quarters_ago(self, n: int) -> dict:
    \"""
    Get the year and quarter corresponding to [n] quarters before the current quarter. The output is a dictionary with the following schema:
        {
            "year": int,
            "quarter": int
        }
    Examples:
        Question:
        What is Microsoft's total revenue in the last 10 quarters?
        Answer:
        microsoft = client.ticker("MSFT")
        latest_periods = client.get_latest()
        latest_year = latest_periods["quarterly"]["latest_year"]
        latest_quarter = latest_periods["quarterly"]["latest_quarter"]
        last_10_quarters = client.get_n_quarters_ago(10)
        total_revenue = microsoft.total_revenue(period_type="quarterly", start_year=last_10_quarters["year"], start_quarter=last_10_quarters["quarter"], end_year=latest_year, end_quarter=latest_quarter)
        total_revenue
    \"""
def ticker(self, identifier: str, exchange_code: Optional[str] = None) -> Ticker:
    \"""
    Returns the Ticker object
    Param identifier (str): Provide either the ticker (the unique ticker symbol, the company's primary security ticker), the ISIN, or the CUSIP that can be used as an identifier for the ticker object.
    Param exchange_code (str): Provide the stock exchange code.
    For example, call the method with a ticker symbol, ISIN, or CUSIN with its respective company name:
        amazon = client.ticker("AMZN")
        Question:
        What is Medibank Private Limited income statement?
        Answer:
        medibank = client.ticker("MPL", "ASX")
        medibank.income_statement()

        Question:
        What is Tata Consultancy balance sheet?
        Answer:
        tata = client.ticker("TCS", "NSEI")
        tata.balance_sheet()

        Question:
        What is Honda's cash flow statement?
        Answer:
        honda = client.ticker("7267")
        honda.cashflow()

        Question:
        What was the EBITDA for CUSIP 550021109 in Q2 2023?
        # Use CUSIP as ticker identifier
        company1_ticker = client.ticker("550021109")
        company1_ebitda = company1_ticker.net_income(start_year=2023, start_quarter=2, end_year=2023, end_quarter=2)
        company1_ebitda

        Question:
        ISIN US45166V2051 net income 2023?
        # Use ISIN as ticker identifier
        company1_ticker = client.ticker("US45166V2051")
        company1_net_income = company1_ticker.net_income(start_year=2023)
        company1_net_income
    \"""
class Ticker:
    \"""
    Attributes:
        history_metadata (dict): A dictionary describing meta information about ticker history with the following keys:
        - currency (str): The currency in which the ticker is traded.
        - symbol (str): The symbol representing the ticker.
        - exchange_name (str): The name of the exchange where the ticker is traded.
        - instrument_type (str): The type of financial instrument.
        - first_trade_date (datetime.date): The date when the ticker was first traded.
        earnings_call_datetimes (list): A list of datetime objects representing company future and historical earnings dates with timezone information.
        isin (str): Company ISIN
        company_id (int)
        security_id (int)
        cusip (str)
        trading_item_id (int): Trading item ID
        name (str): The name of the company.
        status (str): The operational status of the company.
        type (str): The type of the company.
        simple_industry (str): The industry in which the company operates.
        number_of_employees (Decimal)
        founding_date (datetime.date)
        webpage (str)
        address (str): The street address of the company.
        city (str)
        zip_code (str)
        state (str)
        country (str)
        iso_country (str)
        info (dict): A dictionary with the following keys:
        - name (str): The name of the company.
        - status (str): The operational status of the company.
        - type (str): The type of the company.
        - simple_industry (str): The industry in which the company operates.
        - number_of_employees (Decimal)
        - founding_date (datetime.date)
        - webpage (str)
        - address (str): The street address of the company.
        - city (str)
        - zip_code (str)
        - state (str)
        - country (str)
        - iso_country (str)
    \"""
    Functions:
    The following functions share the same signature, parameters and return shape.

    Here is the general signature of the functions:
    def function_name(period_type: Optional[str] = None, start_year: Optional[int] = None, end_year: Optional[int] = None, start_quarter: Optional[int] = None, end_quarter: Optional[int] = None) -> pd.DataFrame:
        \"""
        Parameters:
            period_type: Optional[str], default to None
            The period type of the data requested.
                Options:
                "annual": For annual data set to "annual"
                "quarterly": For quarterly data set to "quarterly"
                "ytd": For year to date data also known as ytd, set to "ytd"
                "ltm": For last twelve months data also known as LTM, set to "ltm"
                If any other values are passed in, the function will error.
            start_year (Optional[int]): The starting year for the data range.
            end_year (Optional[int]): The ending year for the data range. If the question is about "the last x years" or the "latest", and end_year is not provided, put end_year as the current year - 1. Otherwise, put the end_year as the current year.
            start_quarter (Optional[int]): The starting quarter (1-4) within the starting year.
            end_quarter (Optional[int]): The ending quarter (1-4) within the ending year.

        Function Names:
            - balance_sheet()
            - income_statement()
            - cash_flow()
            - revenue()
            - finance_division_revenue()
            - insurance_division_revenue()
            - revenue_from_sale_of_assets()
            - revenue_from_sale_of_investments()
            - revenue_from_interest_and_investment_income()
            - other_revenue()
            - total_other_revenue()
            - fees_and_other_income()
            - total_revenue()
            - cost_of_goods_sold()
            - finance_division_operating_expense()
            - insurance_division_operating_expense()
            - finance_division_interest_expense()
            - cost_of_revenue()
            - gross_profit()
            - selling_general_and_admin_expense()
            - exploration_and_drilling_costs()
            - provision_for_bad_debts()
            - pre_opening_costs()
            - total_selling_general_and_admin_expense()
            - research_and_development_expense()
            - depreciation_and_amortization()
            - amortization_of_goodwill_and_intangibles()
            - impairment_of_oil_gas_and_mineral_properties()
            - total_depreciation_and_amortization()
            - other_operating_expense()
            - total_other_operating_expense()
            - total_operating_expense()
            - operating_income()
            - interest_expense()
            - interest_and_investment_income()
            - net_interest_expense()
            - income_from_affiliates()
            - currency_exchange_gains()
            - other_non_operating_income()
            - total_other_non_operating_income()
            - ebt_excluding_unusual_items()
            - restructuring_charges()
            - merger_charges()
            - merger_and_restructuring_charges()
            - impairment_of_goodwill()
            - gain_from_sale_of_assets()
            - gain_from_sale_of_investments()
            - asset_writedown()
            - in_process_research_and_development_expense()
            - insurance_settlements()
            - legal_settlements()
            - other_unusual_items()
            - total_other_unusual_items()
            - total_unusual_items()
            - ebt_including_unusual_items()
            - income_tax_expense()
            - earnings_from_continued_operations()
            - earnings_from_discontinued_operations()
            - extraordinary_item_and_accounting_change()
            - net_income_to_company()
            - minority_interest_in_earnings()
            - net_income()
            - premium_on_redemption_of_preferred_stock()
            - preferred_stock_dividend()
            - other_preferred_stock_adjustments()
            - other_adjustments_to_net_income()
            - preferred_dividends_and_other_adjustments()
            - net_income_allocable_to_general_partner()
            - net_income_to_common_shareholders_including_extra_items()
            - net_income_to_common_shareholders_excluding_extra_items()
            - cash_and_equivalents()
            - short_term_investments()
            - trading_asset_securities()
            - total_cash_and_short_term_investments()
            - accounts_receivable()
            - other_receivables()
            - notes_receivable()
            - total_receivables()
            - inventory()
            - prepaid_expense()
            - finance_division_loans_and_leases_short_term()
            - finance_division_other_current_assets()
            - loans_held_for_sale()
            - deferred_tax_asset_current_portion()
            - restricted_cash()
            - other_current_assets()
            - total_current_assets()
            - gross_property_plant_and_equipment()
            - accumulated_depreciation()
            - net_property_plant_and_equipment()
            - long_term_investments()
            - goodwill()
            - other_intangibles()
            - finance_division_loans_and_leases_long_term()
            - finance_division_other_non_current_assets()
            - long_term_accounts_receivable()
            - long_term_loans_receivable()
            - long_term_deferred_tax_assets()
            - long_term_deferred_charges()
            - other_long_term_assets()
            - total_assets()
            - accounts_payable()
            - accrued_expenses()
            - short_term_borrowings()
            - current_portion_of_long_term_debt()
            - current_portion_of_capital_leases()
            - current_portion_of_long_term_debt_and_capital_leases()
            - finance_division_debt_current_portion()
            - finance_division_other_current_liabilities()
            - current_income_taxes_payable()
            - current_unearned_revenue()
            - current_deferred_tax_liability()
            - other_current_liability()
            - total_current_liabilities()
            - long_term_debt()
            - capital_leases()
            - finance_division_debt_non_current_portion()
            - finance_division_other_non_current_liabilities()
            - non_current_unearned_revenue()
            - pension_and_other_post_retirement_benefit()
            - non_current_deferred_tax_liability()
            - other_non_current_liabilities()
            - total_liabilities()
            - preferred_stock_redeemable()
            - preferred_stock_non_redeemable()
            - preferred_stock_convertible()
            - preferred_stock_other()
            - preferred_stock_additional_paid_in_capital()
            - preferred_stock_equity_adjustment()
            - treasury_stock_preferred_stock_convertible()
            - treasury_stock_preferred_stock_non_redeemable()
            - treasury_stock_preferred_stock_redeemable()
            - total_preferred_equity()
            - common_stock()
            - additional_paid_in_capital()
            - retained_earnings()
            - treasury_stock()
            - other_equity()
            - total_common_equity()
            - total_equity()
            - total_liabilities_and_equity()
            - common_shares_outstanding()
            - adjustments_to_cash_flow_net_income()
            - other_amortization()
            - total_other_non_cash_items()
            - net_decrease_in_loans_originated_and_sold()
            - provision_for_credit_losses()
            - loss_on_equity_investments()
            - stock_based_compensation()
            - tax_benefit_from_stock_options()
            - net_cash_from_discontinued_operation()
            - other_operating_activities()
            - change_in_trading_asset_securities()
            - change_in_accounts_receivable()
            - change_in_inventories()
            - change_in_accounts_payable()
            - change_in_unearned_revenue()
            - change_in_income_taxes()
            - change_in_deferred_taxes()
            - change_in_other_net_operating_assets()
            - change_in_net_operating_assets()
            - cash_from_operations()
            - capital_expenditure()
            - sale_of_property_plant_and_equipment()
            - cash_acquisitions()
            - divestitures()
            - sale_of_real_estate()
            - sale_of_intangible_assets()
            - net_cash_from_investments()
            - net_decrease_in_investment_loans_originated_and_sold()
            - other_investing_activities()
            - total_other_investing_activities()
            - cash_from_investing()
            - short_term_debt_issued()
            - long_term_debt_issued()
            - total_debt_issued()
            - short_term_debt_repaid()
            - long_term_debt_repaid()
            - total_debt_repaid()
            - issuance_of_common_stock()
            - repurchase_of_common_stock()
            - issuance_of_preferred_stock()
            - repurchase_of_preferred_stock()
            - common_dividends_paid()
            - preferred_dividends_paid()
            - total_dividends_paid()
            - special_dividends_paid()
            - other_financing_activities()
            - cash_from_financing()
            - foreign_exchange_rate_adjustments()
            - miscellaneous_cash_flow_adjustments()
            - net_change_in_cash()
            - depreciation()
            - depreciation_of_rental_assets()
            - sale_proceeds_from_rental_assets()
            - basic_eps()
            - basic_eps_excluding_extra_items()
            - basic_eps_from_accounting_change()
            - basic_eps_from_extraordinary_items()
            - basic_eps_from_accounting_change_and_extraordinary_items()
            - weighted_average_basic_shares_outstanding()
            - diluted_eps()
            - diluted_eps_excluding_extra_items()
            - weighted_average_diluted_shares_outstanding()
            - normalized_basic_eps()
            - normalized_diluted_eps()
            - dividends_per_share()
            - distributable_cash_per_share()
            - diluted_eps_from_accounting_change_and_extraordinary_items()
            - diluted_eps_from_accounting_change()
            - diluted_eps_from_extraordinary_items()
            - diluted_eps_from_discontinued_operations()
            - funds_from_operations()
            - ebitda()
            - ebita()
            - ebit()
            - ebitdar()
            - net_debt()
            - effective_tax_rate()
            - current_ratio()
            - quick_ratio()
            - total_debt_to_capital()
            - net_working_capital()
            - working_capital()
            - change_in_net_working_capital()
            - total_debt()
            - total_debt_to_equity_ratio()
        Returns:
            A Pandas DataFrame with column headers as a string with the time period.
            For quarterly, ytd, or ltm data: <Year>'Q'<Quarter>, such as '2023Q4'.
            For annual data: <Year>, such as '2021'.
            For example, to access the value for 2023Q3, use df['2023Q3']. Or to access into year 2021, use df['2021'].

        Examples:
            Question:
            What is the return on equity for IBM from 2020 to 2023?
            Answer:
            ibm = client.ticker("IBM")
            net_income = ibm.net_income(start_year=2020, end_year=2023)
            total_equity = ibm.total_equity(start_year=2020, end_year=2023)
            roe = net_income.reset_index(drop=True) / total_equity.reset_index(drop=True)
            roe

            Question:
            What is the revenue CAGR for META from 2019 to 2023?
            Answer:
            meta = client.ticker("META")
            revenue = meta.revenue(start_year=2019, end_year = 2023)
            cagr = (revenue['2023'] / revenue['2019']) ** (1/4) - 1
            cagr

            Question:
            What is BoFa's gross profit in the last 4 years?
            Answer:
            bac = client.ticker("BAC")
            # Don't have information for the current year, so check last year
            end_year = datetime.date.today().year - 1
            gross_profit = bac.gross_profit(start_year=end_year - 4, end_year=end_year)
            gross_profit

            Question:
            What is Chipotle's working capital from 2019 to 2021?
            Answer:
            chipotle = client.ticker("CMG")
            working_capital = chipotle.working_capital(start_year=2019, end_year=2021)
            working_capital

            Question:
            What is the percentage change in gross profit for Microsoft from 2021 to now?
            Answer:
            microsoft = client.ticker("MSFT")
            end_year = datetime.date.today().year - 1
            gross_profit = microsoft.gross_profit(start_year=2021, end_year=end_year)
            percentage_change = (gross_profit[str(end_year)] - gross_profit["2021"]) / gross_profit["2021"] * 100
            percentage_change

            Question:
            What is Airbnb's quick ratio quarterly for the last 4 years?
            Answer:
            airbnb = client.ticker("ABNB")
            quick_ratio = airbnb.quick_ratio(period_type="quarterly", start_year=datetime.datetime.now().year - 4, end_year=datetime.datetime.now().year)
            quick_ratio

            Question:
            LTM EBITDA from Q3 of 2022 to Q1 of 2024 for Exxon?
            Answer:
            exxon = client.ticker("XOM")
            ebitda = exxon.ebitda(period_type="ltm", start_year=2022, start_quarter=3, end_year=2024, end_quarter=1)
            ebitda

            Question:
            What is Verizon's year to date capex?
            Answer:
            verizon = client.ticker("VZ")
            capital_expenditure = verizon.capital_expenditure(period_type="ytd")
            capital_expenditure
        \"""

    Functions:
    The following functions `history` and `price_chart` share the same parameters.

    def history(self, periodicity: Optional[str] = "day", adjusted: Optional[bool] = True, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    Retrieves the historical price data for a given asset over a specified date range.
        Returns:
            A pd.DataFrame containing historical price data with columns corresponding to the specified periodicity,
            with Date as the index, and columns "open", "high", "low", "close", "volume" in type decimal.
            The Date index is a string that depends on the periodicity.
            If periodicity="day", the Date index is the day in format "YYYY-MM-DD", eg "2024-05-13".
            If periodicity="week", the Date index is the week number of the year in format "YYYY Week ##", eg "2024 Week 2".
            If periodicity="month", the Date index is the month name of the year in format "<Month> YYYY", eg "January 2024".
            If periodicity="year", the Date index is the year in format "YYYY", eg "2024".

    def price_chart(self, periodicity: Optional[str] = "day", adjusted: Optional[bool] = True, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Image:
    Retrieves the plotted historical price data for a given asset over a specified date range as an Image.
        Returns:
            An Image object with the plotted price data.
        \"""
        Shared Parameters of function `history` and `price_chart`:
            periodicity: Optional[str], default "day"
            The frequency or interval at which the historical data points are sampled or aggregated. Periodicity is not the same as the date range. The date range specifies the time span over which the data is retrieved, while periodicity determines how the data within that date range is aggregated.
                Options:
                "day": Data points are returned for each day within the specified date range.
                "week": Data points are aggregated weekly, with each row representing a week.
                "month": Data points are aggregated monthly, with each row representing a month.
                "year": Data points are aggregated yearly, with each row representing a year.
            adjusted: Optional[bool], default True
            Whether to retrieve adjusted prices that account for corporate actions such as dividends and splits.
            start_date: Optional[str], default None
            The start date for historical price retrieval in format "YYYY-MM-DD".
            end_date: Optional[str], default None
            The end date for historical price retrieval in format "YYYY-MM-DD".
            If end_date is not specified, put end_date as today.

        Examples:
            Question:
            What were Apple's prices for the the last 3 weeks?
            Answer:
            from dateutil.relativedelta import relativedelta
            apple = client.ticker("AAPL")
            end_date = datetime.date.today()
            start_date = end_date - datetime.relativedelta(days=3*7)
            prices = apple.history(periodicity="day", start_date=str(start_date), end_date=str(end_date))
            prices

            Question:
            What was Nvidia's prices for the last 2 years on a weekly basis?
            Answer:
            from dateutil.relativedelta import relativedelta
            nvda = client.ticker("NVDA")
            end_date = datetime.date.today()
            start_date = end_date - datetime.relativedelta(days=2*365)
            prices = nvda.history(periodicity="week", start_date=str(start_date), end_date=str(end_date))
            prices
        \"""
""".replace("XXXX", str(datetime.now().year))
