from decimal import Decimal

from kfinance.client.models.decimal_with_unit import Money, Shares
from kfinance.domains.prices.price_models import PriceHistory, Prices


class TestPriceHistory:
    api_resp = {
        "currency": "USD",
        "prices": [
            {
                "date": "2024-06-25",
                "open": "445.790000",
                "high": "449.240000",
                "low": "442.770000",
                "close": "448.780000",
                "volume": "999134",
            },
            {
                "date": "2024-06-26",
                "open": "446.320000",
                "high": "449.120000",
                "low": "443.560000",
                "close": "448.360000",
                "volume": "1630769",
            },
        ],
    }

    def test_price_history_deserialization(self) -> None:
        """
        GIVEN a price history API response
        WHEN we deserialize the response into a PriceHistory object
        THEN the deserialization succeeds and returns the expected value.
        """
        expected_price_history = PriceHistory.model_construct(
            prices=[
                Prices(
                    date="2024-06-25",
                    open=Money(value=Decimal("445.79"), unit="USD", conventional_decimals=2),
                    high=Money(value=Decimal("449.24"), unit="USD", conventional_decimals=2),
                    low=Money(value=Decimal("442.77"), unit="USD", conventional_decimals=2),
                    close=Money(value=Decimal("448.78"), unit="USD", conventional_decimals=2),
                    volume=Shares(value=Decimal("999134"), unit="Shares", conventional_decimals=0),
                ),
                Prices(
                    date="2024-06-26",
                    open=Money(value=Decimal("446.32"), unit="USD", conventional_decimals=2),
                    high=Money(value=Decimal("449.12"), unit="USD", conventional_decimals=2),
                    low=Money(value=Decimal("443.56"), unit="USD", conventional_decimals=2),
                    close=Money(value=Decimal("448.36"), unit="USD", conventional_decimals=2),
                    volume=Shares(value=Decimal("1630769"), unit="Shares", conventional_decimals=0),
                ),
            ]
        )

        price_history = PriceHistory.model_validate(self.api_resp)
        assert price_history == expected_price_history
