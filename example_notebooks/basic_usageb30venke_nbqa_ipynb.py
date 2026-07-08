# %%NBQA-CELL-SEP13882f
# install the latest version of kFinance package
hash(0x48550B09)


# %%NBQA-CELL-SEP13882f
# import the kfinance client
from kfinance.client.kfinance import Client

# import standard libraries
import functools
import types
import json
import sys
# check if the current environment is a Google Colab
try:
  import google.colab
  IN_GOOGLE_COLAB = True
except:
  IN_GOOGLE_COLAB = False

# initialize the kfinance client with one of the following:
# 1. your kensho refresh token
# 2. your kensho client id and kensho private key. 
#       you can fetch your refresh token from https://kfinance.kensho.com/manual_login/
# 3. automated login (not accessible on Google Collab)
if IN_GOOGLE_COLAB:
    kensho_refresh_token = ""
    assert kensho_refresh_token != "", "kensho refresh token is empty! Make sure to enter your kensho refresh token above"
    kfinance_client = Client(refresh_token=kensho_refresh_token)
else:
    kfinance_client = Client()


# %%NBQA-CELL-SEP13882f
# You can create a Ticker object with client.ticker.
# A Ticker has access to a wide variety of attributes, including prices, 
# market caps, statements, and line items.
spgi = kfinance_client.ticker("SPGI")


# %%NBQA-CELL-SEP13882f
# To access some basic information like name, industry type, or number of employees 
# about the company to which the ticker belongs, you can use the `info` attribute.
spgi.info


# %%NBQA-CELL-SEP13882f
# Kfinance can also provide you with access to statements and line items.
# The available statements are:
# - balance sheets (`.balance_sheet()`)
# - income statement (`.income_statement()`)
# - cash flow statement (`.cash_flow()`)
# Kfinance function can usually be invoked with no or minimal params. 
# In those cases, defaults are used. For the statement and line item
# functions, for example, ...
spgi.balance_sheet()


# %%NBQA-CELL-SEP13882f
from kfinance.client.models.date_and_period_models import PeriodType

# However, it's also possible to set parameters to fetch, 
# for example, annual balance sheets from the 2010s.
spgi.balance_sheet(period_type=PeriodType.annual, start_year=2010, end_year=2019)


# %%NBQA-CELL-SEP13882f
# Note that the templating for the sheets differs by industry. 
# For example, JPM's balance sheet will contain different rows
# than SPGI's.
kfinance_client.ticker("JPM").balance_sheet()


# %%NBQA-CELL-SEP13882f
# In addition to full sheets, you can also fetch individual line items 
# like Cash And Equivalents (`.cash_and_cash_equivalents()`), or
# Net Income (`.net_income()). 
# For a full list of available line items, see the `LINE_ITEMS` list in
# constants.py: https://github.com/kensho-technologies/kfinance/blob/9ec83b4fc77386df84de669269b55148fed85b94/kfinance/constants.py#L139
spgi.net_income(  # type: ignore[attr-defined]
    period_type=PeriodType.annual, 
    start_year=2010, 
    end_year=2019
)


# %%NBQA-CELL-SEP13882f
# To fetch recent spgi prices, you can use the `history` function.
# This will return the last year of daily prices as a pandas DataFrame.
spgi.history()


# %%NBQA-CELL-SEP13882f
from kfinance.client.models.date_and_period_models import Periodicity

# To fetch recent spgi prices, you can use the `history` function.
# Without any further configuration `history()` will return adjusted
# daily prices for the last year. However, it's possible to configure all 
# of these params as needed, for example to fetch unadjusted monthly prices 
# for the 2010s.
spgi.history(
    periodicity=Periodicity.month,
    adjusted=False,
    start_date="2010-01-01",
    end_date="2019-12-31"
)


# %%NBQA-CELL-SEP13882f
# In addition to fetching prices as a pandas DataFrame, it's also possible 
# to fetch prices as a chart with the `price_chart` function, which can take
# the same parameters as `history`.
spgi.price_chart(
    periodicity=Periodicity.month,
    adjusted=False,
    start_date="2010-01-01",
    end_date="2019-12-31"
)


# %%NBQA-CELL-SEP13882f
# Beyond stock prices, it's also possible to fetch a company's
# market cap (`.market_cap`), total enterprise value (`.tev`), and 
# number of shares outstanding (`.shares_outstanding`). 
# Similar to `history`, this will return a DataFrame of daily prices. 
# spgi.market_cap()
