from typing import Type

import pytest

from kfinance.kfinance import Client
from kfinance.mcp import build_doc_string
from kfinance.tool_calling import ALL_TOOLS
from kfinance.tool_calling.shared_models import KfinanceTool


class TestDocStringBuilding:
    @pytest.mark.parametrize("tool_class", ALL_TOOLS)
    def test_build_doc_string(self, mock_client: Client, tool_class: Type[KfinanceTool]):
        tool = tool_class(kfinance_client=mock_client)
        build_doc_string(tool)
