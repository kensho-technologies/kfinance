from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.kfinance import Company, MergerOrAcquisition, ParticipantInMerger
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_identifiers import (
    CompanyId,
    fetch_company_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolArgsWithIdentifiers,
)


class GetMergersFromIdentifier(KfinanceTool):
    name: str = "get_mergers_from_identifiers"
    description: str = dedent("""
        Get the transaction IDs that involve the given identifiers.

        For example, "Which companies did Microsoft purchase?" or "Which company bought Ben & Jerrys?"
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, identifiers: list[str]) -> dict:
        api_client = self.kfinance_client.kfinance_api_client
        parsed_identifiers = parse_identifiers(identifiers=identifiers, api_client=api_client)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=api_client
        )

        tasks = [
            Task(
                func=api_client.fetch_mergers_for_company,
                kwargs=dict(company_id=company_id),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        merger_responses = process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)

        return {str(identifier): mergers for identifier, mergers in merger_responses.items()}


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
                    "company_id": str(
                        CompanyId(
                            company_id=merger_participants["target"].company.company_id,
                            api_client=self.kfinance_client.kfinance_api_client,
                        )
                    ),
                    "company_name": merger_participants["target"].company.name,
                },
                "buyers": [
                    {
                        "company_id": str(
                            CompanyId(
                                buyer.company.company_id,
                                api_client=self.kfinance_client.kfinance_api_client,
                            )
                        ),
                        "company_name": buyer.company.name,
                    }
                    for buyer in merger_participants["buyers"]
                ],
                "sellers": [
                    {
                        "company_id": str(
                            CompanyId(
                                seller.company.company_id,
                                api_client=self.kfinance_client.kfinance_api_client,
                            )
                        ),
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
                    "advisor_company_id": str(
                        CompanyId(
                            company_id=advisor.company.company_id,
                            api_client=self.kfinance_client.kfinance_api_client,
                        )
                    ),
                    "advisor_company_name": advisor.company.name,
                    "advisor_type_name": advisor.advisor_type_name,
                }
                for advisor in advisors
            ]
        else:
            return []
