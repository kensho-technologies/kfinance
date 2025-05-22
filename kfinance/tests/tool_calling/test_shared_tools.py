from datetime import datetime

import time_machine

from kfinance.kfinance import Client
from kfinance.tool_calling import GetLatest, GetNQuartersAgo
from kfinance.tool_calling.shared_tools.get_latest import GetLatestArgs
from kfinance.tool_calling.shared_tools.get_n_quarters_ago import GetNQuartersAgoArgs


class TestGetLatest:
    @time_machine.travel(datetime(2025, 1, 1, 12, tzinfo=datetime.now().astimezone().tzinfo))
    def test_get_latest(self, mock_client: Client):
        """
        GIVEN the GetLatest tool
        WHEN request latest info
        THEN we get back latest info
        """

        expected_resp = {
            "annual": {"latest_year": 2024},
            "now": {
                "current_date": "2025-01-01",
                "current_month": 1,
                "current_quarter": 1,
                "current_year": 2025,
            },
            "quarterly": {"latest_quarter": 4, "latest_year": 2024},
        }
        tool = GetLatest(kfinance_client=mock_client)
        resp = tool.run(GetLatestArgs().model_dump(mode="json"))
        assert resp == expected_resp


class TestGetNQuartersAgo:
    @time_machine.travel(datetime(2025, 1, 1, 12, tzinfo=datetime.now().astimezone().tzinfo))
    def test_get_n_quarters_ago(self, mock_client: Client):
        """
        GIVEN the GetNQuartersAgo tool
        WHEN we request 3 quarters ago
        THEN we get back 3 quarters ago
        """

        expected_resp = {"quarter": 2, "year": 2024}
        tool = GetNQuartersAgo(kfinance_client=mock_client)
        resp = tool.run(GetNQuartersAgoArgs(n=3).model_dump(mode="json"))
        assert resp == expected_resp
