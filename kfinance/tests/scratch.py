from constants import IdentificationTriple

from kfinance.kfinance import Client, Tickers


client = Client(refresh_token="foo")

t1: IdentificationTriple = IdentificationTriple(
    company_id=1,
    security_id=1,
    trading_item_id=1
)
t2: IdentificationTriple = IdentificationTriple(
    company_id=2,
    security_id=2,
    trading_item_id=2
)
t3: IdentificationTriple = IdentificationTriple(
    company_id=3,
    security_id=3,
    trading_item_id=3
)


tickers1_2 = Tickers(
    kfinance_api_client=client.kfinance_api_client,
    id_triples=[t1, t2]
)

tickers2_3 = Tickers(
    kfinance_api_client=client.kfinance_api_client,
    id_triples=[t2, t3]
)

intersect = tickers1_2 & tickers2_3

inter = tickers1_2.intersection(tickers2_3, tickers2_3)



a = 10
