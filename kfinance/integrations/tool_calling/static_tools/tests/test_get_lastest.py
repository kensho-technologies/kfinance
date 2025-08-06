from datetime import datetime

import time_machine

from kfinance.client.kfinance import Client
from kfinance.integrations.tool_calling.static_tools.get_latest import GetLatest, GetLatestArgs


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
