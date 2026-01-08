from datetime import date
from textwrap import dedent
from typing import Literal, Type

from pydantic import BaseModel, Field

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.rounds_of_funding.rounds_of_funding_models import (
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
        default=None, description="Limit to top N funding rounds by sort order"
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
        Retrieves funding round OVERVIEWS: transaction_ids, types, dates, basic notes. This is STEP 1 of a MANDATORY two-step process for most funding round questions.

        ⚠️ DOMAIN IDENTIFICATION - USE THIS TOOL WHEN:
        The question is about FUNDING ROUNDS / CAPITAL RAISING / FINANCING activities:
        • Keywords: "funding", "capital", "raise", "raised", "investment", "financing", "round", "Series A/B/C", "seed", "venture"
        • Phrases: "pre-deal context", "need for capital", "use of proceeds", "operating situation" (in context of fundraising)
        • Questions about: Valuations, pricing, investor participation, funding amounts, fundraising history

        ❌ DO NOT use this tool for M&A deals, mergers, acquisitions, or exits (use merger tools instead)
        ❌ DO NOT use this tool for general company information unrelated to fundraising (use company info tools instead)

        WHAT THIS RETURNS: Basic round summaries (transaction_ids, funding_type, closed_date, brief notes in funding_round_notes)
        WHAT THIS DOESN'T RETURN: Detailed terms, advisors, board seats, fees, governance rights, liquidation preferences, participation terms, anti-dilution terms, use of proceeds, detailed investor information, exact pricing/valuation data, security features, pre-deal financial context

        ⚠️ CRITICAL TWO-STEP WORKFLOW:
        Most questions about funding rounds REQUIRE both calls:
        STEP 1: Call THIS function → get transaction_ids
        STEP 2: IMMEDIATELY call get_rounds_of_funding_info_from_transaction_ids with those transaction_ids
        STEP 3: Formulate answer using data from BOTH calls

        ⚠️⚠️ DO NOT SKIP STEP 2 - DO NOT answer after STEP 1 alone if the question asks about ANY of these (STEP 2 is MANDATORY):
        • Pricing/valuation trends - "up-rounds", "down-rounds", "price direction", "share price", "valuation trend", "price per share"
        • Exact valuations - "pre-money valuation", "post-money valuation" (exact numbers, not approximations from notes)
        • Security details - "preferred shares", "convertible", "securities issued", "classes of stock", "series", "share features", "participation", "seniority"
        • Advisors/counsel - "Who advised?", "Which firm represented?", "What counsel?", "legal advisor", "financial advisor"
        • Board seats or governance - "Did X get board seat?", "board representation", "governance rights"
        • Liquidation terms - "liquidation preference", "liquidation price", "multiple", "participating preferred", "cap"
        • Security terms - "anti-dilution", "redemption rights", "dividends", "reorganization clauses"
        • Fees - "advisory fees", "legal fees", "underwriting fees"
        • Use of proceeds - "how will they use", "what will funds be used for", "pre-deal context", "need for capital"
        • Investor contributions - "how much did [investor] contribute", "investor ownership", "investment amount", "lead investor details"
        • Transaction specifics - "upsizing", "offering changes", "tranches", "textual notes", "non-standard terms"

        ⚠️ CRITICAL: The funding_round_notes field in STEP 1 may contain SOME information but it is UNSTRUCTURED and INCOMPLETE. Even if funding_round_notes mentions pricing or terms, you MUST still call STEP 2 to get structured, complete data. DO NOT rely on funding_round_notes alone for questions requiring specific details.

        ROLE PARAMETER USAGE:
        • role='{RoundsOfFundingRole.company_raising_funds}': When asking about a COMPANY that received funding
          Examples: "What rounds did Stripe raise?", "When did Databricks close Series C?", "Show me OpenAI's funding history"
          → Use the TARGET COMPANY's identifier

        • role='{RoundsOfFundingRole.company_investing_in_round_of_funding}': When asking from the INVESTOR's perspective
          Examples: "Which companies did Sequoia invest in?", "What rounds did Benchmark participate in?", "Which firms did Apple invest in?"
          → Use the INVESTOR's identifier

        ⚠️ CRITICAL IDENTIFIER SELECTION FOR INVESTOR CONTRIBUTION QUESTIONS:
        When the question asks "How much did [INVESTOR] contribute/invest in [COMPANY]'s round?":
        • The PRIMARY entity is the INVESTOR (the subject performing the action)
        • Use the INVESTOR's identifier, NOT the company's identifier
        • Use role='{RoundsOfFundingRole.company_investing_in_round_of_funding}'
        • Examples:
          - "How much did Blackbird VC contribute to Morse Micro's Series C?" → identifier=Blackbird VC, role=company_investing_in_round_of_funding
          - "What did Sequoia invest in Stripe's Series B?" → identifier=Sequoia, role=company_investing_in_round_of_funding
          - "How much did Y Combinator put into Airbnb?" → identifier=Y Combinator, role=company_investing_in_round_of_funding

        ENTITY SELECTION PATTERN:
        • "What legal counsel did [INVESTOR] use in their investment in [COMPANY]?" → Use INVESTOR's identifier with role='{RoundsOfFundingRole.company_investing_in_round_of_funding}'
        • "What legal counsel did [COMPANY] use when [INVESTOR] invested?" → Use COMPANY's identifier with role='{RoundsOfFundingRole.company_raising_funds}'
        • "X's investment in Y" → X is the identifier (X is the investor)
        • "X contributed to Y's round" → X is the identifier (X is the investor)
        • "When X invested in Y" → X is the identifier (X is the investor)

        TEMPORAL FILTERING (for "recent" rounds):
        • If question mentions "recent": Use limit parameter to get top N (default N=5) with sort_order="desc"
        • If question specifies timeframe: Use start_date/end_date parameters
        • Examples: "recent investments by X" → limit=5, sort_order="desc"; "investments in last 2 years" → start_date=<2 years ago>

        Supports temporal filtering (start_date, end_date), sorting by date (asc/desc), and limiting (top N).
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
        Retrieves DETAILED transaction information. This is STEP 2 of the MANDATORY two-step workflow for most funding round questions.

        ⚠️ CRITICAL: This function MUST be called after get_rounds_of_funding_from_identifiers when questions require specific details (see list below).

        WORKFLOW:
        STEP 1: Call get_rounds_of_funding_from_identifiers → receive transaction_ids
        STEP 2: Call THIS function → get detailed transaction data
        STEP 3: Synthesize answer from BOTH responses

        PASSING TRANSACTION IDs - THREE SCENARIOS:

        1. DEFAULT (Most Common): Pass ALL transaction_ids from STEP 1
           • Questions about "all rounds", "each round", "across rounds", or asking about details without specifying which round
           • Example: "What is the liquidation preference across all of Company X's funding rounds?"
           • ✓ DO: Pass ALL transaction_ids, then analyze/filter results AFTER receiving the data
           • ✗ DON'T: Pre-filter transaction_ids before this call

        2. FILTERED (When Question Specifies Criteria): Pass ALL first, then can filter if question explicitly specifies
           • Questions like "any round with upsizing", "rounds that included board seats"
           • Can pass all transaction_ids and filter results, OR filter based on basic data before calling
           • Example: "Did any round include board seats?" → Pass all, check board_seat_granted in results

        3. SPECIFIC (When Question Names Exact Rounds): Pass only specified transaction_ids
           • Questions explicitly naming rounds: "Series A", "the 2020 round", "most recent round"
           • Example: "What was the liquidation preference in Company X's Series C?" → Pass only Series C transaction_id

        RULE OF THUMB: When in doubt, pass ALL transaction_ids. The API is efficient and filtering results is safer than pre-filtering inputs.

        UNIQUE DETAILS (ONLY available in this call, NOT in get_rounds_of_funding_from_identifiers):
        • ✓ Advisor information: Legal counsel, financial advisors, underwriters (names, firms, fees, lead status)
        • ✓ Board seats: board_seat_granted flag for each investor
        • ✓ Governance rights: Voting rights, ownership thresholds, control provisions
        • ✓ Liquidation preferences: liquidation_preference type (Senior/Pari-Passu), liquidation_preference_multiple
        • ✓ Security terms: Anti-dilution methods, participation rights, caps, redemption terms, cumulative dividends
        • ✓ Valuation details: Exact pre_money_valuation, post_money_valuation (not approximations from notes)
        • ✓ Use of proceeds: Detailed use_of_proceeds descriptions
        • ✓ Transaction specifics: Upsizing (upsized_amount, offering_size_change), tranches, amendments
        • ✓ Investor details: Individual investor investment amounts, ownership percentages, lead investor status
        • ✓ Fee breakdowns: Legal fees, underwriting fees, other fees (separate amounts)

        WHEN THIS TOOL IS MANDATORY (cannot answer from STEP 1 alone):
        • Questions about PRICING/VALUATION TRENDS: "up-round", "down-round", "price direction", "valuation trend", "flat round", "share price trend", "price per share"
        • Questions about SECURITY DETAILS: "preferred shares", "securities issued", "classes", "convertible", "participation", "cap", "seniority", "share features"
        • Questions about ADVISORS: "advisor", "counsel", "legal", "underwriter", "financial advisor", "which firm", "who represented"
        • Questions about GOVERNANCE: "board seat", "board representation", "governance", "voting rights"
        • Questions about LIQUIDATION TERMS: "liquidation preference", "liquidation price", "multiple", "participating preferred"
        • Questions about SECURITY TERMS: "anti-dilution", "redemption", "dividend", "reorganization"
        • Questions about EXACT VALUATIONS: "pre-money valuation", "post-money valuation" (exact numbers)
        • Questions about USE OF PROCEEDS: "use of proceeds", "how will", "what will funds", "pre-deal", "need for capital", "operating situation", "financial context"
        • Questions about INVESTOR DETAILS: "how much did [investor] contribute", "investor ownership", "investment amount", "lead investor"
        • Questions about TRANSACTION DETAILS: "upsizing", "upsize", "offering change", "textual notes", "non-standard terms", "strategic motivations"
        • Questions about FEES: advisory fees, legal fees, underwriting fees

        Examples:
        ✓ MANDATORY STEP 2:
          - "What is the funding price direction trend for RunBuggy—up-rounds or down-rounds?" (needs pricing from all rounds)
          - "Did Sky Safe issue participating preferred shares with a cap in Series C?" (needs security terms)
          - "What classes of securities were issued by BOXABL?" (needs security details)
          - "Are there textual notes indicating non-standard terms across Waymo's rounds?" (needs detailed transaction notes)
          - "Did Kensho outline pre-deal operating situations?" (needs use_of_proceeds field)
          - "How much did Neuralink raise in Series B?" (needs exact transaction.amount_offered)
          - "What was the post-money valuation for EliseAI's Series E?" (needs exact transaction.post_money_valuation)
          - "How much did Blackbird VC contribute to Morse Micro's Series C?" (needs investor.investment_value)
        ✗ OPTIONAL STEP 2: "When did Stripe close Series E?" (date in overview), "How many rounds did Databricks raise?" (count in overview)
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
                                    "advisor_company_id": "C_286743412",
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
                                "ownership_percentage_pre": 0.0000
                                "ownership_percentage_post": 25.0000
                                "board_seat_granted": True,
                                "advisors": [
                                    {
                                        "advisor_company_id": "C_22439",
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
        round_of_info_with_advisors = {}
        for transaction_id, round_of_info in round_of_info_responses.items():
            target_key = AdvisorTaskKey(
                transaction_id=transaction_id,
                role=RoundsOfFundingRole.company_raising_funds,
                company_id=round_of_info.participants.target.company_id,
            )
            target_advisors_resp = advisor_responses.get(target_key.to_string())
            target_advisors = target_advisors_resp.advisors if target_advisors_resp else []

            investor_advisors = {}
            for investor in round_of_info.participants.investors:
                investor_key = AdvisorTaskKey(
                    transaction_id=transaction_id,
                    role=RoundsOfFundingRole.company_investing_in_round_of_funding,
                    company_id=investor.company_id,
                )
                advisor_resp = advisor_responses.get(investor_key.to_string())
                investor_advisors[investor.company_id] = (
                    advisor_resp.advisors if advisor_resp else []
                )

            # Create round info with advisors
            round_of_info_with_advisors[transaction_id] = round_of_info.with_advisors(
                target_advisors=target_advisors, investor_advisors=investor_advisors
            )

        return GetRoundsOfFundingInfoFromTransactionIdsResp(
            results=round_of_info_with_advisors,
            errors=[],  # Individual API failures would be captured in process_tasks_in_thread_pool_executor
        )


class GetFundingSummaryFromIdentifiersArgs(ToolArgsWithIdentifiers):
    pass  # Only needs identifiers, no additional args needed


class GetFundingSummaryFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, FundingSummary]


class GetFundingSummaryFromIdentifiers(KfinanceTool):
    name: str = "get_funding_summary_from_identifiers"
    description: str = dedent("""
        Get AGGREGATED funding statistics for specified company identifiers. Returns high-level summaries only: total capital raised, total rounds count, first and most recent funding dates, and breakdown of rounds by type.

        WHAT THIS RETURNS: Aggregate statistics ONLY (total_capital_raised sum, total_rounds count, date ranges, rounds_by_type breakdown)
        WHAT THIS DOESN'T RETURN: Individual round details, transaction info, terms, advisors, investors, specific round amounts, round-by-round data

        ⚠️ CRITICAL LIMITATION: This tool provides ONLY aggregate statistics. It does NOT return individual round data needed for verification, analysis, or questions requiring round-by-round information.

        TOOL SELECTION DECISION TREE:

        1. Question asks for SIMPLE AGGREGATES (and ONLY aggregates)? → Use THIS tool
           • "How much TOTAL capital has X raised?" (single aggregate number)
           • "How many rounds did X complete?" (single count)
           • "When was X's first/most recent funding?" (date range only)
           • "What types of rounds has X raised?" (type breakdown only)

        2. Question asks about "CUMULATIVE", "ACROSS ALL ROUNDS", or needs VERIFICATION? → Use get_rounds_of_funding_from_identifiers (NOT this tool)
           • ❌ "What is the CUMULATIVE amount raised by X across all disclosed rounds?" → Use get_rounds_of_funding_from_identifiers
           • ❌ "How much capital has X raised ACROSS all rounds?" → Use get_rounds_of_funding_from_identifiers
           • WHY: Even though these sound like aggregates, they require seeing individual rounds to:
             - Verify which rounds are included in the sum
             - Check data completeness
             - Handle currency conversions across rounds
             - Filter rounds by criteria (e.g., "disclosed rounds", "equity rounds")
           • THIS tool only returns a pre-calculated sum that may be incomplete or null

        3. Question asks about SPECIFIC rounds or ANY round details? → Use get_rounds_of_funding_from_identifiers
           • "What was X's Series A amount?"
           • "Show me X's funding history" (needs individual rounds)
           • "When did X raise their last round?" (needs specific round info)
           • "Which rounds did X raise?"
           • "List X's funding rounds"
           • ANY question that needs round-by-round information

        4. Question asks about DETAILED terms, advisors, or governance? → Use get_rounds_of_funding_from_identifiers + get_rounds_of_funding_info_from_transaction_ids
           • See those tools' descriptions for when the two-step process is mandatory

        FALLBACK BEHAVIOR:
        ⚠️⚠️ If this tool returns 0 rounds, null total_capital_raised, or incomplete data, you MUST follow up with get_rounds_of_funding_from_identifiers to verify whether funding data actually exists. The summary is often incomplete while individual round data is available.

        Common scenario: Summary shows 0 rounds but actual rounds exist in the detailed endpoint.
        → Solution: ALWAYS try get_rounds_of_funding_from_identifiers as a fallback when summary is empty/incomplete.

        Examples:
        ✓ Use THIS tool: "How much total capital has Instacart raised?" (IF you only need the aggregate and don't need to verify/analyze individual rounds)
        ✗ DON'T use this:
          - "What is the cumulative amount of capital raised by Ramp across all disclosed rounds?" → Use get_rounds_of_funding_from_identifiers
          - "How much has X raised across all rounds?" → Use get_rounds_of_funding_from_identifiers
          - "What was Stripe's Series A amount?" (specific round)
          - "Which rounds included board seats?" (needs details)
          - "Show me X's funding rounds" (needs individual round list)
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
