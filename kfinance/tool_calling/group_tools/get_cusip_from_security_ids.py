from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.kfinance import Securities, Security
from kfinance.tool_calling.shared_models import KfinanceTool


class GetCusipFromSecurityIdsArgs(BaseModel):
    security_ids: list[int]


class GetCusipFromSecurityIds(KfinanceTool):
    name: str = "get_cusip_from_security_ids"
    description: str = "Get the CUSIPs for a group of security_ids."
    args_schema: Type[BaseModel] = GetCusipFromSecurityIdsArgs
    required_permission: Permission | None = Permission.IDPermission
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(self, security_ids: list[int]) -> dict[str, str]:
        securities = Securities(
            kfinance_api_client=self.kfinance_client.kfinance_api_client, security_ids=security_ids
        )

        fetched_results: dict[Security, str | None] = securities.cusip  # type:ignore[attr-defined]
        stringified_results = dict()
        for security, cusip in fetched_results.items():
            stringified_results[f"security_id: {security.security_id}"] = f"CUSIP: {cusip}"

        return stringified_results
