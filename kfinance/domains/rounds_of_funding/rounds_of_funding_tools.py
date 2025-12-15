from datetime import date
from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
    AdvisorsResp,
    AdvisorTaskKey,
    FundingSummary,
    RoundOfFundingInfo,
    RoundOfFundingInfoWithAdvisors,
    RoundsOfFundingResp,
    RoundsOfFundingRole,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetRoundsofFundingFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    role: RoundsOfFundingRole
    start_date: date | None = Field(
        default=None,
        description="Filter rounds to those closed on or after this date (YYYY-MM-DD format)",
    )
    end_date: date | None = Field(
        default=None,
        description="Filter rounds to those closed on or before this date (YYYY-MM-DD format)",
    )
    limit: int | None = Field(
        default=None, description="Limit to N most recent funding rounds (based on closed_date)"
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort order for funding rounds by closed_date. 'desc' shows most recent first, 'asc' shows oldest first",
    )


class GetRoundsOfFundingFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, RoundsOfFundingResp]


class GetRoundsOfFundingFromIdentifiers(KfinanceTool):
    name: str = "get_rounds_of_funding_from_identifiers"
    description: str = dedent(f"""
        "Retrieves rounds of funding for each specified company identifier that is either of `role` {RoundsOfFundingRole.company_raising_funds} or {RoundsOfFundingRole.company_investing_in_round_of_funding}. Provides the transaction_id, funding_round_notes, funding_type, and transaction closed_date (finalization). Supports temporal filtering by start_date and end_date (inclusive), sorting by closed_date (desc=most recent first, asc=oldest first), and limiting to N most recent rounds. Use this tool to answer questions like 'What was the completion date of the funding of Nasdaq Private Market, LLC by Citigroup Inc.', 'What was the latest funding round for ElevenLabs?', 'What were Microsoft's 3 most recent investments?', 'What funding rounds did Microsoft participate in during 2023?', or 'Which Series A rounds did Sequoia Capital invest in between 2020 and 2022?'"
    """).strip()
    args_schema: Type[BaseModel] = GetRoundsofFundingFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(
        self,
        identifiers: list[str],
        role: RoundsOfFundingRole,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> GetRoundsOfFundingFromIdentifiersResp:
        """Sample Response:

        {
            'results': {
                'SPGI': {
                    "rounds_of_funding": [
                        {
                            "transaction_id": 334220,
                            "funding_round_notes": "Kensho Technologies Inc. announced that it has received funding from new investor, Impresa Management LLC in 2013.",
                            "closed_date": "2013-12-31",
                            "funding_type": "Series A",
                        },
                        {
                            "transaction_id": 242311,
                            "funding_round_notes": "Kensho Technologies Inc. announced that it will receive $740,000 in funding on January 29, 2014. The company will issue convertible debt securities in the transaction. The company will issue securities pursuant to exemption provided under Regulation D.",
                            "closed_date": "2014-02-13",
                            "funding_type": "Convertible Note",
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
                func=api_client.fetch_rounds_of_funding_for_company
                if role is RoundsOfFundingRole.company_raising_funds
                else api_client.fetch_rounds_of_funding_for_investing_company,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        rounds_of_funding_responses: dict[str, RoundsOfFundingResp] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )

        if start_date or end_date:
            filtered_responses = {}
            for identifier, response in rounds_of_funding_responses.items():
                filtered_rounds = []
                for round_of_funding in response.rounds_of_funding:
                    # Skip rounds without a closed_date if filtering by date
                    if round_of_funding.closed_date is None:
                        continue

                    if start_date and round_of_funding.closed_date < start_date:
                        continue
                    if end_date and round_of_funding.closed_date > end_date:
                        continue

                    filtered_rounds.append(round_of_funding)

                filtered_responses[identifier] = RoundsOfFundingResp(
                    rounds_of_funding=filtered_rounds
                )

            rounds_of_funding_responses = filtered_responses

        final_responses = {}
        for identifier, response in rounds_of_funding_responses.items():
            rounds = response.rounds_of_funding

            # Sort by closed_date (putting None dates at the end)
            if sort_order == "desc":
                rounds.sort(key=lambda r: r.closed_date or date.min, reverse=True)
            else:
                rounds.sort(key=lambda r: r.closed_date or date.max, reverse=False)

            if limit is not None:
                rounds = rounds[:limit]

            final_responses[identifier] = RoundsOfFundingResp(rounds_of_funding=rounds)

        return GetRoundsOfFundingFromIdentifiersResp(
            results=final_responses, errors=list(id_triple_resp.errors.values())
        )


class GetRoundsOfFundingInfoFromTransactionIdsArgs(BaseModel):
    transaction_ids: list[int] = Field(
        description="List of transaction IDs for rounds of funding.", min_length=1
    )


class GetRoundsOfFundingInfoFromTransactionIdsResp(ToolRespWithErrors):
    results: dict[int, RoundOfFundingInfoWithAdvisors]


class GetRoundsOfFundingInfoFromTransactionIds(KfinanceTool):
    name: str = "get_rounds_of_funding_info_from_transaction_ids"
    description: str = dedent("""
        "Provides comprehensive information for multiple rounds of funding at once, including for each round of funding its timeline (announced date, closed date), participants' company_name and company_id (target and investors), funding_type, amount_offered, fees, amounts etc. Use this tool to answer questions like 'How much did Harvey raise in their Series D?', 'Who were Google's angel investors?', 'What was the total amount raised across all of Anysphere's funding rounds?', 'What is the liquidation price reported in each funding round for Anysphere?', 'What is the announcement date of the funding of Veza Technologies, Inc by JPMorgan Chase & Co?'. Always call this for announcement or transaction value related questions."
    """).strip()
    args_schema: Type[BaseModel] = GetRoundsOfFundingInfoFromTransactionIdsArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, transaction_ids: list[int]) -> GetRoundsOfFundingInfoFromTransactionIdsResp:
        """Sample Response:

        {
            'results': {
                334220: {
                    "timeline": {
                        "announced_date": "2013-12-01",
                        "closed_date": "2013-12-31"
                    },
                    "participants": {
                        "target": {
                            "company_id": "C_12345",
                            "company_name": "Kensho Technologies Inc.",
                            "advisors": [
                                {
                                    "advisor_company_id": 286743412,
                                    "advisor_company_name": "PJT Partners Inc.",
                                    "advisor_type_name": "Financial Adviser",
                                    "advisor_fee_amount": "2500000.0000",
                                    "advisor_fee_currency": "USD",
                                    "is_lead": true
                                },
                            ],
                        },
                        "investors": [
                            {
                                "company_id": "C_67890",
                                "company_name": "Impresa Management LLC",
                                "lead_investor": True,
                                "investment_value": 5000000.00,
                                "currency": "USD",
                                "advisors": [
                                    {
                                        "advisor_company_id": 22439,
                                        "advisor_company_name": "DLA Piper LLP (US)",
                                        "advisor_type_name": "Legal Counsel",
                                        "advisor_fee_amount": "3750000.0000",
                                        "advisor_fee_currency": "USD",
                                        "is_lead": true
                                    },
                                ]
                            }
                        ]
                    },
                    "transaction": {
                        "funding_type": "Series A",
                        "amount_offered": 5000000.00,
                        "currency_name": "USD",
                        "legal_fees": 150000.00,
                        "other_fees": 75000.00,
                        "pre_money_valuation": 15000000.00,
                        "post_money_valuation": 20000000.00
                    },
                    "security": {...}
                },
                242311: { ... }
            },
            'errors': []
        }
        """
        api_client = self.kfinance_client.kfinance_api_client

        round_of_info_tasks = [
            Task(
                func=api_client.fetch_round_of_funding_info,
                kwargs=dict(transaction_id=transaction_id),
                result_key=transaction_id,
            )
            for transaction_id in transaction_ids
        ]
        round_of_info_responses: dict[int, RoundOfFundingInfo] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=round_of_info_tasks)
        )

        advisor_tasks = []

        for transaction_id, round_of_info in round_of_info_responses.items():
            target_key = AdvisorTaskKey(
                transaction_id=transaction_id,
                role=RoundsOfFundingRole.company_raising_funds,
                company_id=round_of_info.participants.target.company_id,
            )
            advisor_tasks.append(
                Task(
                    func=api_client.fetch_advisors_for_company_raising_round_of_funding,
                    kwargs=dict(
                        transaction_id=transaction_id,
                    ),
                    result_key=target_key.to_string(),
                )
            )

            for investor in round_of_info.participants.investors:
                investor_key = AdvisorTaskKey(
                    transaction_id=transaction_id,
                    role=RoundsOfFundingRole.company_investing_in_round_of_funding,
                    company_id=investor.company_id,
                )
                advisor_tasks.append(
                    Task(
                        func=api_client.fetch_advisors_for_company_investing_in_round_of_funding,
                        kwargs=dict(
                            transaction_id=transaction_id,
                            advised_company_id=investor_key.company_id,
                        ),
                        result_key=investor_key.to_string(),
                    )
                )

        advisor_responses = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=advisor_tasks
        )

        # Merge advisor data into round of funding info
        round_info_with_advisors = {}
        for transaction_id, round_of_info in round_of_info_responses.items():
            target_key = AdvisorTaskKey(
                transaction_id=transaction_id,
                role=RoundsOfFundingRole.company_raising_funds,
                company_id=round_of_info.participants.target.company_id,
            )
            target_advisors = advisor_responses.get(
                target_key.to_string(), AdvisorsResp(advisors=[])
            ).advisors

            investor_advisors = {}
            for investor in round_of_info.participants.investors:
                investor_key = AdvisorTaskKey(
                    transaction_id=transaction_id,
                    role=RoundsOfFundingRole.company_investing_in_round_of_funding,
                    company_id=investor.company_id,
                )
                if investor_key.to_string() in advisor_responses:
                    investor_advisors[investor.company_id] = advisor_responses[
                        investor_key.to_string()
                    ].advisors

            # Create round info with advisors
            round_info_with_advisors[transaction_id] = round_of_info.with_advisors(
                target_advisors=target_advisors, investor_advisors=investor_advisors
            )

        return GetRoundsOfFundingInfoFromTransactionIdsResp(
            results=round_info_with_advisors,
            errors=[],  # Individual API failures would be captured in process_tasks_in_thread_pool_executor
        )


class GetFundingSummaryFromIdentifiersArgs(ToolArgsWithIdentifiers):
    pass  # Only needs identifiers, no additional args needed


class GetFundingSummaryFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, FundingSummary]


class GetFundingSummaryFromIdentifiers(KfinanceTool):
    name: str = "get_funding_summary_from_identifiers"
    description: str = dedent("""
        "Get aggregated funding statistics for specified company identifiers without fetching individual rounds. Returns total capital raised, total rounds count, first and most recent funding dates, and breakdown of rounds by type. Ideal for cumulative questions that require summary statistics. Use this tool to answer questions like 'How much total capital did Anysphere raise across all its funding rounds to date?', 'What is the total capital raised by Ramp across all disclosed rounds?', or 'How many funding rounds has Neuralink completed?'"
    """).strip()
    args_schema: Type[BaseModel] = GetFundingSummaryFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(self, identifiers: list[str]) -> GetFundingSummaryFromIdentifiersResp:
        """Get funding summary for companies by aggregating their rounds of funding data."""
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_rounds_of_funding_for_company,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        rounds_of_funding_responses: dict[str, RoundsOfFundingResp] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )

        all_transaction_ids = []
        identifier_to_transaction_ids = {}

        for identifier, response in rounds_of_funding_responses.items():
            transaction_ids = [r.transaction_id for r in response.rounds_of_funding]
            all_transaction_ids.extend(transaction_ids)
            identifier_to_transaction_ids[identifier] = transaction_ids

        detail_tasks = [
            Task(
                func=api_client.fetch_round_of_funding_info,
                kwargs=dict(transaction_id=transaction_id),
                result_key=transaction_id,
            )
            for transaction_id in all_transaction_ids
        ]

        detailed_round_info: dict[int, RoundOfFundingInfo] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=detail_tasks
        )

        summaries = {}
        for identifier, response in rounds_of_funding_responses.items():
            rounds = response.rounds_of_funding
            company_transaction_ids = identifier_to_transaction_ids[identifier]

            total_rounds = len(rounds)
            dates = [r.closed_date for r in rounds if r.closed_date is not None]
            first_funding_date = min(dates) if dates else None
            most_recent_funding_date = max(dates) if dates else None

            rounds_by_type: dict[str, int] = {}
            for round_of_funding in rounds:
                funding_type = round_of_funding.funding_type or "Unknown"
                rounds_by_type[funding_type] = rounds_by_type.get(funding_type, 0) + 1

            total_capital_raised = None
            currency = None
            for transaction_id in company_transaction_ids:
                if transaction_id in detailed_round_info:
                    round_detail = detailed_round_info[transaction_id]
                    if (
                        total_capital_raised is None or currency is None
                    ) and round_detail.transaction.aggregate_amount_raised:
                        total_capital_raised = float(
                            round_detail.transaction.aggregate_amount_raised
                        )
                        currency = round_detail.transaction.currency

            summaries[identifier] = FundingSummary(
                company_id=identifier,
                total_capital_raised=total_capital_raised,
                total_capital_raised_currency=currency,
                total_rounds=total_rounds,
                first_funding_date=first_funding_date,
                most_recent_funding_date=most_recent_funding_date,
                rounds_by_type=rounds_by_type,
                sources=[
                    {
                        "notes": "total_rounds, first_funding_date, most_recent_funding_date, and rounds_by_type are derived from underlying rounds of funding data that might be non-comprehensive."
                    }
                ],
            )

        return GetFundingSummaryFromIdentifiersResp(
            results=summaries, errors=list(id_triple_resp.errors.values())
        )
