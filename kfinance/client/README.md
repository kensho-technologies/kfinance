# Client

Client contains the main Kfinance `Client` class from `kfinance.py`
and the lower level `KFinanceApiClient` from `fetch.py`. It also
includes the objects like `Company` on which the `Client` operates 
and related helpers like batch processing functionality. 

It may at some point make sense to factor out objects and fetch 
functions into their related domains.