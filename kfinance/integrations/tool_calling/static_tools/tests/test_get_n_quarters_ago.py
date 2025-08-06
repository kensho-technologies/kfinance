from datetime import datetime

import time_machine

from kfinance.client.kfinance import Client
from kfinance.integrations.tool_calling.static_tools.get_n_quarters_ago import (
    GetNQuartersAgo,
    GetNQuartersAgoArgs,
)


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
