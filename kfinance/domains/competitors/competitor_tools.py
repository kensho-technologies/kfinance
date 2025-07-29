from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_identifiers import (
    Identifier,
    fetch_company_ids_from_identifiers,
    parse_identifiers,
)
from kfinance.domains.competitors.competitor_models import CompetitorResponse, CompetitorSource
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
)


class GetCompetitorsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    competitor_source: CompetitorSource


class GetCompetitorsFromIdentifiers(KfinanceTool):
    name: str = "get_competitors_from_identifiers"
    description: str = "Retrieves a list of company_id and company_name that are competitors for a list of companies, optionally filtered by the source of the competitor information."
    args_schema = GetCompetitorsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.CompetitorsPermission}

    def _run(
        self,
        identifiers: list[str],
        competitor_source: CompetitorSource,
    ) -> dict:
        """Sample response:

        {
            SPGI: {
                {'company_id': "C_35352", 'company_name': 'The Descartes Systems Group Inc.'},
                {'company_id': "C_4003514", 'company_name': 'London Stock Exchange Group plc'}
            }
        }
        """

        api_client = self.kfinance_client.kfinance_api_client
        parsed_identifiers = parse_identifiers(identifiers=identifiers, api_client=api_client)
        identifiers_to_company_ids = fetch_company_ids_from_identifiers(
            identifiers=parsed_identifiers, api_client=api_client
        )

        tasks = [
            Task(
                func=api_client.fetch_competitors,
                kwargs=dict(company_id=company_id, competitor_source=competitor_source),
                result_key=identifier,
            )
            for identifier, company_id in identifiers_to_company_ids.items()
        ]

        competitor_responses: dict[Identifier, CompetitorResponse] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )
        return {
            str(identifier): competitors.model_dump(mode="json")
            for identifier, competitors in competitor_responses.items()
        }
