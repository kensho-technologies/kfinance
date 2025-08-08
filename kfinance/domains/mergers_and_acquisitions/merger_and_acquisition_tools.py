from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.kfinance import Company, MergerOrAcquisition, ParticipantInMerger
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_models import prefix_company_id
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import MergersResp
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetMergersFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, MergersResp]


class GetMergersFromIdentifiers(KfinanceTool):
    name: str = "get_mergers_from_identifiers"
    description: str = dedent("""
        Get the transaction IDs that involve the given identifiers.

        For example, "Which companies did Microsoft purchase?" or "Which company bought Ben & Jerrys?"
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, identifiers: list[str]) -> dict:
        """Sample Response:

        {
            'results': {
                'SPGI': {
                    'target': [
                        {
                            'transaction_id': 10998717,
                            'merger_title': 'Closed M/A of Microsoft Corporation',
                            'closed_date': '2021-01-01'
                        }
                    ],
                    'buyer': [
                        {
                           'transaction_id': 517414,
                           'merger_title': 'Closed M/A of MongoMusic, Inc.',
                           'closed_date': '2023-01-01'
                        },
                    'seller': [
                        {
                            'transaction_id': 455551,
                            'merger_title': 'Closed M/A of VacationSpot.com, Inc.',
                            'closed_date': '2024-01-01'
                        },
                    ]
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }

        """

        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_mergers_for_company,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        merger_responses: dict[str, MergersResp] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        output_model = GetMergersFromIdentifiersResp(
            results=merger_responses, errors=list(id_triple_resp.errors.values())
        )
        return output_model.model_dump(mode="json")


class GetMergerInfoFromTransactionIdArgs(BaseModel):
    transaction_id: int | None = Field(description="The ID of the transaction.", default=None)


class GetMergerInfoFromTransactionId(KfinanceTool):
    name: str = "get_merger_info_from_transaction_id"
    description: str = dedent("""
        Get the timeline, the participants, and the consideration of the merger or acquisition from the given transaction ID.

        For example, "How much was Ben & Jerrys purchased for?" or "What was the price per share for LinkedIn?" or "When did S&P purchase Kensho?"
    """).strip()
    args_schema: Type[BaseModel] = GetMergerInfoFromTransactionIdArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, transaction_id: int) -> dict:
        merger_or_acquisition = MergerOrAcquisition(
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
            transaction_id=transaction_id,
            merger_title=None,
            closed_date=None,
        )
        merger_timeline = merger_or_acquisition.get_timeline
        merger_participants = merger_or_acquisition.get_participants
        merger_consideration = merger_or_acquisition.get_consideration

        return {
            "timeline": [
                {"status": timeline["status"], "date": timeline["date"].strftime("%Y-%m-%d")}
                for timeline in merger_timeline.to_dict(orient="records")
            ]
            if merger_timeline is not None
            else None,
            "participants": {
                "target": {
                    "company_id": prefix_company_id(
                        merger_participants["target"].company.company_id
                    ),
                    "company_name": merger_participants["target"].company.name,
                },
                "buyers": [
                    {
                        "company_id": prefix_company_id(buyer.company.company_id),
                        "company_name": buyer.company.name,
                    }
                    for buyer in merger_participants["buyers"]
                ],
                "sellers": [
                    {
                        "company_id": prefix_company_id(seller.company.company_id),
                        "company_name": seller.company.name,
                    }
                    for seller in merger_participants["sellers"]
                ],
            }
            if merger_participants is not None
            else None,
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
            }
            if merger_consideration is not None
            else None,
        }


class GetAdvisorsForCompanyInTransactionFromIdentifierArgs(ToolArgsWithIdentifier):
    transaction_id: int | None = Field(description="The ID of the merger.", default=None)


class GetAdvisorsForCompanyInTransactionFromIdentifier(KfinanceTool):
    name: str = "get_advisors_for_company_in_transaction_from_identifier"
    description: str = 'Get the companies advising a company in a given transaction. For example, "Who advised S&P Global during their purchase of Kensho?"'
    args_schema: Type[BaseModel] = GetAdvisorsForCompanyInTransactionFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, identifier: str, transaction_id: int) -> list:
        ticker = self.kfinance_client.ticker(identifier)
        participant_in_merger = ParticipantInMerger(
            kfinance_api_client=ticker.kfinance_api_client,
            transaction_id=transaction_id,
            company=Company(
                kfinance_api_client=ticker.kfinance_api_client,
                company_id=ticker.company.company_id,
            ),
        )
        advisors = participant_in_merger.advisors

        if advisors:
            return [
                {
                    "advisor_company_id": prefix_company_id(advisor.company.company_id),
                    "advisor_company_name": advisor.company.name,
                    "advisor_type_name": advisor.advisor_type_name,
                }
                for advisor in advisors
            ]
        else:
            return []
