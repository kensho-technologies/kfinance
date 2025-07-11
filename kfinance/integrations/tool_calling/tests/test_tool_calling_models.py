import contextlib
from contextlib import nullcontext as does_not_raise

from pydantic import BaseModel, ValidationError
import pytest
from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.companies.company_tools import GetInfoFromIdentifiers
from kfinance.integrations.tool_calling.tool_calling_models import ValidQuarter


class TestGetEndpointsFromToolCallsWithGrounding:
    def test_get_info_from_identifier_with_grounding(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN a KfinanceTool tool
        WHEN we run the tool with `run_with_grounding`
        THEN we get back endpoint urls in addition to the usual tool response.
        """

        # truncated from the original
        resp_data = {"name": "S&P Global Inc.", "status": "Operating"}
        resp_endpoint = [
            "https://kfinance.kensho.com/api/v1/id/SPGI",
            "https://kfinance.kensho.com/api/v1/info/21719",
        ]
        expected_resp = {"data": {"SPGI": resp_data}, "endpoint_urls": resp_endpoint}

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=resp_data,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = tool.run_with_grounding(identifiers=["SPGI"])
        assert resp == expected_resp


class TestValidQuarter:
    class QuarterModel(BaseModel):
        quarter: ValidQuarter | None

    @pytest.mark.parametrize(
        "input_quarter, expectation, expected_quarter",
        [
            pytest.param(1, does_not_raise(), 1, id="int input works"),
            pytest.param("1", does_not_raise(), 1, id="str input works"),
            pytest.param(None, does_not_raise(), None, id="None input works"),
            pytest.param(5, pytest.raises(ValidationError), None, id="invalid int raises"),
            pytest.param("5", pytest.raises(ValidationError), None, id="invalid str raises"),
        ],
    )
    def test_valid_quarter(
        self,
        input_quarter: int | str | None,
        expectation: contextlib.AbstractContextManager,
        expected_quarter: int | None,
    ) -> None:
        """
        GIVEN a model that uses `ValidQuarter`
        WHEN we deserialize with int, str, or None
        THEN valid str get coerced to int. Invalid values raise.
        """
        with expectation:
            res = self.QuarterModel.model_validate(dict(quarter=input_quarter))
            assert res.quarter == expected_quarter
