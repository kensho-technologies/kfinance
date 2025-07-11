from datetime import date
from decimal import Decimal

from kfinance.client.models.decimal_with_unit import Money, Shares
from kfinance.domains.capitalizations.capitalization_models import (
    Capitalization,
    Capitalizations,
    DailyCapitalization,
)


class TestCapitalizations:
    api_resp = {
        "currency": "USD",
        "market_caps": [
            {
                "date": "2024-06-24",
                "market_cap": "139231113000.000000",
                "tev": "153942113000.000000",
                "shares_outstanding": 312900000,
            },
            {
                "date": "2024-06-25",
                "market_cap": "140423262000.000000",
                "tev": "155134262000.000000",
                "shares_outstanding": 312900000,
            },
        ],
    }

    def test_capitalizations_deserialization(self) -> None:
        """
        GIVEN a capitalizations API response
        WHEN we deserialize the response into a Capitalizations object
        THEN the deserialization succeeds and returns the expected value.
        """

        expected_capitalizations = Capitalizations.model_construct(
            capitalizations=[
                DailyCapitalization(
                    date=date(2024, 6, 24),
                    market_cap=Money(
                        value=Decimal("139231113000.00"), unit="USD", conventional_decimals=2
                    ),
                    tev=Money(
                        value=Decimal("153942113000.00"), unit="USD", conventional_decimals=2
                    ),
                    shares_outstanding=Shares(
                        value=Decimal("312900000"), unit="Shares", conventional_decimals=0
                    ),
                ),
                DailyCapitalization(
                    date=date(2024, 6, 25),
                    market_cap=Money(
                        value=Decimal("140423262000.00"), unit="USD", conventional_decimals=2
                    ),
                    tev=Money(
                        value=Decimal("155134262000.00"), unit="USD", conventional_decimals=2
                    ),
                    shares_outstanding=Shares(
                        value=Decimal("312900000"), unit="Shares", conventional_decimals=0
                    ),
                ),
            ]
        )

        assert Capitalizations.model_validate(self.api_resp) == expected_capitalizations

    def test_single_attribute_serialization(self):
        """
        GIVEN a Capitalizations object
        WHEN we only want to dump a single attribute like market_cap
        THEN that attribute gets returned in an LLM-readable, jsonifyable dict format
        """
        expected_serialization = [
            {"date": "2024-06-24", "market_cap": {"unit": "USD", "value": "139231113000.00"}},
            {"date": "2024-06-25", "market_cap": {"unit": "USD", "value": "140423262000.00"}},
        ]
        capitalizations = Capitalizations.model_validate(self.api_resp)
        serialized = capitalizations.model_dump_json_single_metric(Capitalization.market_cap)
        assert serialized == expected_serialization
