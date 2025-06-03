from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool


class GetTranscriptArgs(BaseModel):
    """Tool argument with a key_dev_id."""

    key_dev_id: int = Field(description="The key dev ID for the earnings call")


class GetTranscript(KfinanceTool):
    name: str = "get_transcript"
    description: str = "Get the raw transcript text for an earnings call by key dev ID."
    args_schema: Type[BaseModel] = GetTranscriptArgs
    required_permission: Permission | None = Permission.EarningsPermission

    def _run(self, key_dev_id: int) -> str:
        transcript = self.kfinance_client.transcript(key_dev_id)
        return transcript.raw
