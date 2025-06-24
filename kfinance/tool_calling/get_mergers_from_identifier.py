from typing import Type

from pydantic import BaseModel

from kfinance.constants import Permission
from kfinance.tool_calling.shared_models import KfinanceTool, ToolArgsWithIdentifier


class GetMergersFromIdentifier(KfinanceTool):
    name: str = "get_mergers_from_identifier"
    description: str = 'Get the transaction IDs that involve the given identifier. For example, "Which companies did Microsoft purchase?" or "Which company bought Ben & Jerrys?"'
    args_schema: Type[BaseModel] = ToolArgsWithIdentifier
    required_permission: Permission | None = Permission.MergersPermission

    def _run(self, identifier: str) -> dict:
        ticker = self.kfinance_client.ticker(identifier)
        mergers_and_acquisitions = ticker.company.mergers_and_acquisitions

        return {
            "target": [
                {
                    "transaction_id": merger_or_acquisition.transaction_id,
                    "merger_title": merger_or_acquisition.merger_title,
                }
                for merger_or_acquisition in mergers_and_acquisitions["target"]
            ],
            "buyer": [
                {
                    "transaction_id": merger_or_acquisition.transaction_id,
                    "merger_title": merger_or_acquisition.merger_title,
                }
                for merger_or_acquisition in mergers_and_acquisitions["buyer"]
            ],
            "seller": [
                {
                    "transaction_id": merger_or_acquisition.transaction_id,
                    "merger_title": merger_or_acquisition.merger_title,
                }
                for merger_or_acquisition in mergers_and_acquisitions["seller"]
            ],
        }
