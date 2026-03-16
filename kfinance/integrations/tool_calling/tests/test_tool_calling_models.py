import asyncio
import contextlib
from contextlib import nullcontext as does_not_raise
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ValidationError
import pytest
from pytest_httpx import HTTPXMock

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
)
from kfinance.domains.business_relationships.business_relationship_tools import (
    GetBusinessRelationshipFromIdentifiers,
    GetBusinessRelationshipFromIdentifiersArgs,
)
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX
from kfinance.domains.companies.company_tools import (
    GetInfoFromIdentifiers,
    GetInfoFromIdentifiersResp,
)
from kfinance.integrations.tool_calling.tool_calling_models import ValidQuarter


class TestGetEndpointsFromToolCallsWithGrounding:
    @pytest.mark.asyncio
    async def test_get_info_from_identifier_with_grounding(
        self, mock_client: Client, httpx_mock: HTTPXMock
    ):
        """
        GIVEN a KfinanceTool tool
        WHEN we run the tool with `run_with_grounding`
        THEN we get back endpoint urls in addition to the usual tool response.
        """

        # truncated from the original
        resp_data = {
            "name": "S&P Global Inc.",
            "status": "Operating",
            "company_id": f"{COMPANY_ID_PREFIX}{SPGI_COMPANY_ID}",
        }
        resp_endpoint = [
            "https://kfinance.kensho.com/api/v1/ids",
            "https://kfinance.kensho.com/api/v1/info/21719",
        ]
        expected_resp = {
            "data": GetInfoFromIdentifiersResp.model_validate({"results": {"SPGI": resp_data}}),
            "endpoint_urls": resp_endpoint,
        }
        del resp_data["company_id"]

        # Mock the /ids endpoint
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/ids",
            match_json={"identifiers": ["SPGI"]},
            json={"data": {"SPGI": SPGI_ID_TRIPLE.model_dump(mode="json")}},
        )

        # Mock the /info endpoint
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=resp_data,
        )

        tool = GetInfoFromIdentifiers(kfinance_client=mock_client)
        resp = await tool.run_with_endpoint_tracking(identifiers=["SPGI"])
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


class TestRunSyncAndAsync:
    def test_run_sync_and_async(self, add_spgi_supplier_mock_resp: None, httpx_client: Any):
        """
        GIVEN a sync environment with sync and async clients (via asyncio.run)
        WHEN requests are made with both sync and async clients in a sync
        THEN all calls return the same results without erroring out.
        """

        args = GetBusinessRelationshipFromIdentifiersArgs(
            identifiers=["SPGI"],
            business_relationship=BusinessRelationshipType.supplier,
        )

        sync_client = Client(refresh_token="foo")
        # Set access token so that the client doesn't try to fetch it.
        sync_client.kfinance_api_client._access_token = "foo"  # noqa: SLF001
        sync_client.kfinance_api_client._access_token_expiry = int(datetime(2100, 1, 1).timestamp())  # noqa: SLF001
        async_client = Client(refresh_token="foo")
        async_client.kfinance_api_client._access_token = "foo"  # noqa: SLF001
        async_client.kfinance_api_client._access_token_expiry = int(  # noqa: SLF001
            datetime(2100, 1, 1).timestamp()
        )

        def run_sync():
            tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=sync_client)
            sync_resp = tool.run(args.model_dump(mode="json"))
            return sync_resp

        async def run_async_twice():
            tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=async_client)
            async_resp1 = await tool.ainvoke(args.model_dump(mode="json"))
            async_resp2 = await tool.ainvoke(args.model_dump(mode="json"))
            return async_resp1, async_resp2

        # Sync calls can be run multiple times (no async loop issues)
        sync_res1 = run_sync()
        sync_res2 = run_sync()

        # Event loop gets closed after asyncio.run, so we run the tool twice in the function
        async_res1, async_res2 = asyncio.run(run_async_twice())

        # Sync calls can still be run after async calls
        sync_res3 = run_sync()
        sync_res4 = run_sync()

        assert sync_res1 == sync_res2 == sync_res3 == sync_res4 == async_res1 == async_res2
