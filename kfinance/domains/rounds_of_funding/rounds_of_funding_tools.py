from textwrap import dedent
from typing import Type

from kfinance.domains.mergers_and_acquisitions.merger_and_acquisition_models import AdvisorResp
from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.kfinance import Company, ParticipantInMerger, ParticipantInRoF
from kfinance.client.permission_models import Permission
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import(
    RoundOfFundingInfo,
    RoundsOfFundingResp,RoundsofFundingRole
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetRoundsofFundingFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    role: RoundsofFundingRole

class GetRoundsOfFundingFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, RoundsOfFundingResp]


class GetRoundsOfFundingFromIdentifiers(KfinanceTool):
    name: str = "get_rounds_of_funding_from_identifiers"
    description: str = dedent("""
        "Retrieves all rounds of funding for each specified company identifier that is either of `role` company_raising_funds or company_investing_in_round_of_funding. Provides the transaction_id, funding_round_notes, and transaction closed_date (finalization). Use this tool to answer questions like 'What was the completion date of the funding of Nasdaq Private Market, LLC by Citigroup Inc.', or 'How many rounds of funding were there for ElevenLabs?'"
    """).strip()
    args_schema: Type[BaseModel] = GetRoundsofFundingFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, identifiers: list[str], role: RoundsofFundingRole) -> GetRoundsOfFundingFromIdentifiersResp:
        """Sample Response:

        {
            'results': {
                'SPGI': {
                    "rounds_of_funding": [
                        {
                            "transaction_id": 334220,
                            "funding_round_notes": "Kensho Technologies Inc. announced that it has received funding from new investor, Impresa Management LLC in 2013.",
                            "closed_date": "2013-12-31",
                        },
                        {
                            "transaction_id": 242311,
                            "funding_round_notes": "Kensho Technologies Inc. announced that it will receive $740,000 in funding on January 29, 2014. The company will issue convertible debt securities in the transaction. The company will issue securities pursuant to exemption provided under Regulation D.",
                            "closed_date": "2014-02-13",
                        },
                    ],
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }

        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        tasks = [
            Task(
                func=api_client.fetch_rounds_of_funding_for_company if role is RoundsofFundingRole.company_raising_funds else api_client.fetch_rounds_of_funding_for_investing_company,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        rounds_of_funding_responses: dict[str, RoundsOfFundingResp] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        return GetRoundsOfFundingFromIdentifiersResp(
            results=rounds_of_funding_responses, errors=list(id_triple_resp.errors.values())
        )


class GetRoundOfFundingInfoFromTransactionIdArgs(BaseModel):
    transaction_id: int | None = Field(description="The transaction ID of the round of funding.", default=None)

class GetRoundOfFundingInfoFromTransactionId(KfinanceTool):
    name: str = "get_round_of_funding_info_from_transaction_id"
    description: str = dedent("""
        "Provides comprehensive information about a round of funding, including its timeline (announced date, closed date), participants' company_name and company_id (target and investors), funding_type, amount_offered, fees, amounts etc. Use this tool to answer questions like 'How much did Harvey raise in their Series D?', 'Who were Google's angel investors?', 'What is the announcement date of the funding of Veza Technologies, Inc by JPMorgan Chase & Co?'. Always call this for announcement or transaction value related questions."
    """).strip()
    args_schema: Type[BaseModel] = GetRoundOfFundingInfoFromTransactionIdArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, transaction_id: int) -> RoundOfFundingInfo:
        return self.kfinance_client.kfinance_api_client.fetch_round_of_funding_info(
            transaction_id=transaction_id
        )


class GetAdvisorsForCompanyInRoundOfFundingFromIdentifierArgs(ToolArgsWithIdentifier):
    transaction_id: int | None = Field(description="The ID of the round of funding.", default=None)
    role: RoundsofFundingRole


class GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp(ToolRespWithErrors):
    results: list[AdvisorResp]


class GetAdvisorsForCompanyInRoundOfFundingFromIdentifier(KfinanceTool):
    name: str = "get_advisors_for_company_in_round_of_funding_from_identifier"
    description: str = dedent("""
        "Returns a list of advisor companies that provided advisory services to the specified company identifier that is either of `role` company_raising_funds or company_investing_in_round_of_funding during a round of funding. Use this tool to answer questions like 
                              'Who advised S&P Global during their purchase of Kensho?', 'Which firms advised Ben & Jerry's in their acquisition?'."
    """).strip()
    args_schema: Type[BaseModel] = GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(
        self, identifier: str, transaction_id: int, role: RoundsofFundingRole
    ) -> GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=[identifier])
        # If the identifier cannot be resolved, return the associated error.
        if id_triple_resp.errors:
            return GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp(
                results=[], errors=list(id_triple_resp.errors.values())
            )

        id_triple = id_triple_resp.identifiers_to_id_triples[identifier]

        round_of_funding = ParticipantInRoF (
            kfinance_api_client=api_client,
            transaction_id=transaction_id,
            company=Company(
                kfinance_api_client=api_client,
                company_id=id_triple.company_id,
            ),
            target=True if role is RoundsofFundingRole.company_raising_funds else False
        )

        advisors = round_of_funding.advisors

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

        return GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp(
            results=advisors_response, errors=list(id_triple_resp.errors.values())
        )
