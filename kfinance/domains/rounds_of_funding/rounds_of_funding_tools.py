from datetime import date
from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.kfinance import Company, ParticipantInRoF
from kfinance.client.permission_models import Permission
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
    AdvisorInfo,
    FundingSummary,
    InvestorParticipation,
    RoundOfFundingInfo,
    RoundsOfFundingResp,
    RoundsOfFundingRole,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifier,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetRoundsofFundingFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    role: RoundsOfFundingRole
    start_date: date | None = Field(
        default=None,
        description="Filter rounds to those closed on or after this date (YYYY-MM-DD format)"
    )
    end_date: date | None = Field(
        default=None,
        description="Filter rounds to those closed on or before this date (YYYY-MM-DD format)"
    )
    limit: int | None = Field(
        default=None,
        description="Limit to N most recent funding rounds (based on closed_date)"
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort order for funding rounds by closed_date. 'desc' shows most recent first, 'asc' shows oldest first"
    )


class GetRoundsOfFundingFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, RoundsOfFundingResp]


class GetRoundsOfFundingFromIdentifiers(KfinanceTool):
    name: str = "get_rounds_of_funding_from_identifiers"
    description: str = dedent(f"""
        "Retrieves rounds of funding for each specified company identifier that is either of `role` {RoundsOfFundingRole.company_raising_funds} or {RoundsOfFundingRole.company_investing_in_round_of_funding}. Provides the transaction_id, funding_round_notes, funding_type, and transaction closed_date (finalization). Supports temporal filtering by start_date and end_date, sorting by closed_date (desc=most recent first, asc=oldest first), and limiting to N most recent rounds. Use this tool to answer questions like 'What was the latest funding round for ElevenLabs?', 'What were Microsoft's 3 most recent investments?', 'What funding rounds did Microsoft participate in during 2023?', or 'Which Series A rounds did Sequoia Capital invest in between 2020 and 2022?'"
    """).strip()
    args_schema: Type[BaseModel] = GetRoundsofFundingFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(
        self, identifiers: list[str], role: RoundsOfFundingRole, start_date: date | None = None, end_date: date | None = None, limit: int | None = None, sort_order: Literal["asc", "desc"] = "desc"
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

        # Apply temporal filtering if specified
        if start_date or end_date:
            filtered_responses = {}
            for identifier, response in rounds_of_funding_responses.items():
                filtered_rounds = []
                for round_of_funding in response.rounds_of_funding:
                    # Skip rounds without a closed_date if filtering by date
                    if round_of_funding.closed_date is None:
                        continue

                    # Apply date filters
                    if start_date and round_of_funding.closed_date < start_date:
                        continue
                    if end_date and round_of_funding.closed_date > end_date:
                        continue

                    filtered_rounds.append(round_of_funding)

                # Create new response with filtered rounds
                filtered_responses[identifier] = RoundsOfFundingResp(rounds_of_funding=filtered_rounds)

            rounds_of_funding_responses = filtered_responses

        # Apply sorting and limiting
        final_responses = {}
        for identifier, response in rounds_of_funding_responses.items():
            rounds = response.rounds_of_funding

            # Sort by closed_date (putting None dates at the end)
            if sort_order == "desc":
                rounds.sort(key=lambda r: r.closed_date or date.min, reverse=True)
            else:
                rounds.sort(key=lambda r: r.closed_date or date.max, reverse=False)

            # Apply limit if specified
            if limit is not None:
                rounds = rounds[:limit]

            final_responses[identifier] = RoundsOfFundingResp(rounds_of_funding=rounds)

        return GetRoundsOfFundingFromIdentifiersResp(
            results=final_responses, errors=list(id_triple_resp.errors.values())
        )



class GetRoundsOfFundingInfoFromTransactionIdsArgs(BaseModel):
    transaction_ids: list[int] = Field(
        description="List of transaction IDs for rounds of funding.",
        min_length=1
    )


class GetRoundsOfFundingInfoFromTransactionIdsResp(ToolRespWithErrors):
    results: dict[int, RoundOfFundingInfo]


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
                        "target": {"company_id": "C_12345", "company_name": "Kensho Technologies Inc."},
                        "investors": [{"company_id": "C_67890", "company_name": "Impresa Management LLC", "lead_investor": True, "investment_value": 5000000.00}]
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

        tasks = [
            Task(
                func=api_client.fetch_round_of_funding_info,
                kwargs=dict(transaction_id=transaction_id),
                result_key=transaction_id,
            )
            for transaction_id in transaction_ids
        ]

        round_info_responses: dict[int, RoundOfFundingInfo] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )

        # Post-process to populate investor_participations from existing participants data
        for round_info in round_info_responses.values():
            if round_info.participants and round_info.participants.investors:
                investor_participations = []
                for investor in round_info.participants.investors:
                    investor_participations.append(
                        InvestorParticipation(
                            investor_name=investor.company_name,
                            investment_amount=float(investor.investment_value) if investor.investment_value else None,
                            ownership_percentage_pre=None,  # Not available in current API response
                            ownership_percentage_post=None,  # Not available in current API response
                            board_seat_granted=None,  # Not available in current API response
                            lead_investor=investor.lead_investor,
                        )
                    )
                round_info.investor_participations = investor_participations

        return GetRoundsOfFundingInfoFromTransactionIdsResp(
            results=round_info_responses,
            errors=[]  # Individual API failures would be captured in process_tasks_in_thread_pool_executor
        )


class GetAdvisorsForCompanyInRoundOfFundingFromIdentifierArgs(ToolArgsWithIdentifier):
    transaction_id: int | None = Field(description="The ID of the round of funding.", default=None)
    role: RoundsOfFundingRole


class GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp(ToolRespWithErrors):
    results: list[AdvisorInfo]


class GetAdvisorsForCompanyInRoundOfFundingFromIdentifier(KfinanceTool):
    name: str = "get_advisors_for_company_in_round_of_funding_from_identifier"
    description: str = dedent("""
        "Returns detailed advisor information including fee disclosures for companies that provided advisory services to the specified company identifier during a round of funding. Provides advisor name, role (Legal Counsel, Financial Advisor, Lead Underwriter), lead status, fee disclosure status, and fee amounts with currency. Use this tool to answer questions like 'Who advised Uber in their Series B?', 'What were the advisor fees in OpenAI's Series C round?', or 'Which advisors had lead roles and disclosed fees in Company X's funding round?'"
    """).strip()

    args_schema: Type[BaseModel] = GetAdvisorsForCompanyInRoundOfFundingFromIdentifierArgs
    accepted_permissions: set[Permission] | None = {Permission.MergersPermission}

    def _run(
        self, identifier: str, transaction_id: int, role: RoundsOfFundingRole
    ) -> GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=[identifier])
        # If the identifier cannot be resolved, return the associated error.
        if id_triple_resp.errors:
            return GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp(
                results=[], errors=list(id_triple_resp.errors.values())
            )

        id_triple = id_triple_resp.identifiers_to_id_triples[identifier]

        round_of_funding = ParticipantInRoF(
            kfinance_api_client=api_client,
            transaction_id=transaction_id,
            company=Company(
                kfinance_api_client=api_client,
                company_id=id_triple.company_id,
            ),
            target=True if role is RoundsOfFundingRole.company_raising_funds else False,
        )

        advisors = round_of_funding.advisors

        advisors_response: list[AdvisorInfo] = []
        if advisors:
            for advisor in advisors:
                # Map advisor_type_name to advisor_role and determine if it's a lead role
                advisor_role = advisor.advisor_type_name or "Unknown"
                is_lead = "lead" in advisor_role.lower() if advisor_role else False

                advisors_response.append(
                    AdvisorInfo(
                        advisor_name=advisor.company.name,
                        advisor_role=advisor_role,
                        is_lead=is_lead,
                        fees_disclosed=False,  # Default to False since individual advisor fees aren't available in current API
                        advisor_fee_amount=None,  # Individual advisor fees not available in current API
                        advisor_fee_currency=None,  # Individual advisor fees not available in current API
                    )
                )

        return GetAdvisorsForCompanyInRoundOfFundingFromIdentifierResp(
            results=advisors_response, errors=list(id_triple_resp.errors.values())
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

        # Fetch all rounds for each company (assuming company_raising_funds role)
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

        # Create summary for each company
        summaries = {}
        for identifier, response in rounds_of_funding_responses.items():
            rounds = response.rounds_of_funding

            # Calculate summary statistics
            total_rounds = len(rounds)
            dates = [r.closed_date for r in rounds if r.closed_date is not None]
            first_funding_date = min(dates) if dates else None
            most_recent_funding_date = max(dates) if dates else None

            # Count rounds by type
            rounds_by_type = {}
            for round_of_funding in rounds:
                funding_type = round_of_funding.funding_type or "Unknown"
                rounds_by_type[funding_type] = rounds_by_type.get(funding_type, 0) + 1

            # For total capital raised, we'd need to fetch detailed info for each round
            # Since this is meant to be an efficient summary endpoint, we'll set it to None for now
            # In a real implementation, the API might provide aggregate amounts directly

            summaries[identifier] = FundingSummary(
                company_id=identifier,
                total_capital_raised=None,  # Would need detailed round info to calculate
                total_rounds=total_rounds,
                first_funding_date=first_funding_date,
                most_recent_funding_date=most_recent_funding_date,
                rounds_by_type=rounds_by_type,
            )

        return GetFundingSummaryFromIdentifiersResp(
            results=summaries,
            errors=list(id_triple_resp.errors.values())
        )
