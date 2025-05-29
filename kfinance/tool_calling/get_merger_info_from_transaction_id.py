from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import Permission
from kfinance.kfinance import MergerOrAcquisition
from kfinance.tool_calling.shared_models import KfinanceTool


class GetMergerInfoFromTransactionIDArgs(BaseModel):
    transaction_id: int | None = Field(description="The ID of the merger.", default=None)


class GetMergerInfoFromTransactionID(KfinanceTool):
    name: str = "get_merger_info_from_transaction_id"
    description: str = 'Get the timeline, the participants, and the consideration of the merger or acquisition from the given transaction ID. For example, "How much was Ben & Jerrys purchased for?" or "What was the price per share for LinkedIn?" or "When did S&P purchase Kensho?"'
    args_schema: Type[BaseModel] = GetMergerInfoFromTransactionIDArgs
    required_permission: Permission | None = Permission.MergersPermission

    def _run(self, transaction_id: int) -> dict:
        merger_or_acquisition = MergerOrAcquisition(
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
            transaction_id=transaction_id,
            merger_title=None,
        )
        merger_timeline = merger_or_acquisition.get_timeline
        merger_participants = merger_or_acquisition.get_participants
        merger_consideration = merger_or_acquisition.get_consideration

        return {
            "timeline": merger_timeline.to_dict(orient="records"),
            "participants": {
                "target": merger_participants["target"].company_id,
                "buyers": [buyer.company_id for buyer in merger_participants["buyers"]],
                "sellers": [seller.company_id for seller in merger_participants["sellers"]],
            },
            "consideration": {
                "currency_name": merger_consideration["currency_name"],
                "current_calculated_gross_total_transaction_value": merger_consideration[
                    "current_calculated_gross_total_transaction_value"
                ],
                "current_calculated_implied_equity_value": merger_consideration[
                    "current_calculated_implied_equity_value"
                ],
                "current_calculated_implied_enterprise_value": merger_consideration[
                    "current_calculated_implied_enterprise_value"
                ],
                "details": merger_consideration["details"].to_dict(orient="records"),
            },
        }
