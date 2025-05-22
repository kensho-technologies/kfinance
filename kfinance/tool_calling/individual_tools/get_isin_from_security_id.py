from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission, ToolMode
from kfinance.tool_calling.shared_models import KfinanceTool


class GetIsinFromSecurityIdArgs(BaseModel):
    security_id: int


class GetIsinFromSecurityId(KfinanceTool):
    name: str = "get_isin_from_security_id"
    description: str = "Get the ISIN associated with a security_id."
    args_schema: Type[BaseModel] = GetIsinFromSecurityIdArgs
    required_permission: Permission | None = Permission.IDPermission
    tool_modes: set[ToolMode] = {ToolMode.INDIVIDUAL}

    def _run(self, security_id: int) -> str:
        return self.kfinance_client.security(security_id).isin
