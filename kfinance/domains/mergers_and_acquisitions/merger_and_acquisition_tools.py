from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.kfinance import Company, ParticipantInMerger
from kfinance.client.permission_models import Permission
from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import (
    AdvisorResp,
    MergerInfo,
    MergersResp,
)
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
        "Retrieves all merger and acquisition transactions involving the specified company identifier for each specified company identifier. The results are categorized by the company's role in each transaction: target, buyer, or seller. Provides the transaction_id, merger_title, and transaction closed_date (finalization) . Use this tool to answer questions like 'Which companies did Microsoft purchase?', 'Which company acquired Ben & Jerry's?', and 'Who did Pfizer acquire?'"
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, identifiers: list[str]) -> GetMergersFromIdentifiersResp:
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
        return GetMergersFromIdentifiersResp(
            results=merger_responses, errors=list(id_triple_resp.errors.values())
        )


class GetMergerInfoFromTransactionIdArgs(BaseModel):
    transaction_id: int | None = Field(description="The ID of the transaction.", default=None)


class GetMergerInfoFromTransactionId(KfinanceTool):
    name: str = "get_merger_info_from_transaction_id"
    description: str = dedent("""
        "Provides comprehensive information about a specific merger or acquisition transaction, including its timeline (announced date, closed date), participants' company_name and company_id (target, buyers, sellers), and financial consideration details (including monetary values). Use this tool to answer questions like 'When was the acquisition Ben & Jerry's announced?', 'What was the transaction size of Vodafone's acquisition of Mannesmann?', 'How much did S&P purchase Kensho for?'. Always call this for announcement related questions"
    """).strip()
    args_schema: Type[BaseModel] = GetMergerInfoFromTransactionIdArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, transaction_id: int) -> MergerInfo:
        return self.kfinance_client.kfinance_api_client.fetch_merger_info(
            transaction_id=transaction_id
        )


class GetAdvisorsForCompanyInTransactionFromIdentifierArgs(ToolArgsWithIdentifier):
    transaction_id: int | None = Field(description="The ID of the merger.", default=None)


class GetAdvisorsForCompanyInTransactionFromIdentifierResp(ToolRespWithErrors):
    results: list[AdvisorResp]


class GetAdvisorsForCompanyInTransactionFromIdentifier(KfinanceTool):
    name: str = "get_advisors_for_company_in_transaction_from_identifier"
    description: str = dedent("""
        "Returns a list of advisor companies that provided advisory services to the specified company during a particular merger or acquisition transaction. Use this tool to answer questions like 'Who advised S&P Global during their purchase of Kensho?', 'Which firms advised Ben & Jerry's in their acquisition?'."
    """).strip()
    args_schema: Type[BaseModel] = GetAdvisorsForCompanyInTransactionFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(
        self, identifier: str, transaction_id: int
    ) -> GetAdvisorsForCompanyInTransactionFromIdentifierResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=[identifier])
        # If the identifier cannot be resolved, return the associated error.
        if id_triple_resp.errors:
            return GetAdvisorsForCompanyInTransactionFromIdentifierResp(
                results=[], errors=list(id_triple_resp.errors.values())
            )

        id_triple = id_triple_resp.identifiers_to_id_triples[identifier]

        participant_in_merger = ParticipantInMerger(
            kfinance_api_client=api_client,
            transaction_id=transaction_id,
            company=Company(
                kfinance_api_client=api_client,
                company_id=id_triple.company_id,
            ),
        )

        advisors = participant_in_merger.advisors

        advisors_response: list[AdvisorResp] = []
        if advisors:
            for advisor in advisors:
                advisors_response.append(
                    AdvisorResp(
                        advisor_company_id=advisor.company.company_id,
                        advisor_company_name=advisor.company.name,
                        advisor_type_name=advisor.advisor_type_name,
                    )
                )

        return GetAdvisorsForCompanyInTransactionFromIdentifierResp(
            results=advisors_response, errors=list(id_triple_resp.errors.values())
        )
