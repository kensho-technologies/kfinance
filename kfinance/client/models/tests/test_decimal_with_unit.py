from decimal import Decimal
from typing import Any

import pytest

from kfinance.client.models.decimal_with_unit import DecimalWithUnit, Money, Shares


class TestDecimalWithUnit:
    @pytest.mark.parametrize(
        "conventional_decimals, input, expected_value",
        [
            pytest.param(2, "0.10", Decimal("0.10"), id="input matches conventional decimals"),
            pytest.param(
                1, "0.10", Decimal("0.1"), id="input more precise than conventional decimals"
            ),
            pytest.param(
                3, "0.10", Decimal("0.100"), id="input less precise than conventional decimals"
            ),
            pytest.param(1, "0.11", Decimal("0.1"), id="input gets rounded if necessary"),
        ],
    )
    def test_quantize_value(
        self, conventional_decimals: int, input: str, expected_value: Decimal
    ) -> None:
        """
        WHEN a DecimalWithUnit gets deserialized
        THEN the value gets quantized to the conventional_decimals
        """
        dwu = DecimalWithUnit.model_validate(
            dict(value=input, conventional_decimals=conventional_decimals, unit="foo")
        )
        assert dwu.value == expected_value


class TestMoney:
    @pytest.mark.parametrize("currency, expected_conventional_decimals", [("USD", 2), ("BIF", 0)])
    def test_conventional_decimals_injection(
        self, currency: str, expected_conventional_decimals: int
    ) -> None:
        """
        GIVEN a value and unit dict
        WHEN we deserialize the dict into a Money object
        THEN the conventional decimals for the currency get injected.
        """

        money = Money.model_validate({"value": 1, "unit": currency})
        assert money.conventional_decimals == expected_conventional_decimals


class TestShares:
    @pytest.mark.parametrize("input", ["1", 1, Decimal(1), {"value": 1}])
    def test_share_deserialization(self, input: Any):
        """
        GIVEN a str, int, decimal, or dict with value key
        WHEN we deserialize the input into a Shares object
        THEN all of these inputs are accepted.
        """
        shares = Shares.model_validate(input)
        assert shares.value == Decimal(1)
