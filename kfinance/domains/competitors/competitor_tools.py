from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.competitors.competitor_models import CompetitorResponse, CompetitorSource
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetCompetitorsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    # no description because the description for enum fields comes from the enum docstring.
    competitor_source: CompetitorSource


class GetCompetitorsFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, CompetitorResponse]


class GetCompetitorsFromIdentifiers(KfinanceTool):
    name: str = "get_competitors_from_identifiers"
    description: str = "Retrieves a list of company_id and company_name that are competitors for a list of companies, optionally filtered by the source of the competitor information."
    args_schema = GetCompetitorsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.CompetitorsPermission}

    def _run(
        self,
        identifiers: list[str],
        competitor_source: CompetitorSource,
    ) -> GetCompetitorsFromIdentifiersResp:
        """Sample response:

        {
            "results": {
                "SPGI": {
                    {'company_id': "C_35352", 'company_name': 'The Descartes Systems Group Inc.'},
                    {'company_id': "C_4003514", 'company_name': 'London Stock Exchange Group plc'}
                }
            },
            'errors': ['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """

        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_competitors,
                kwargs=dict(company_id=id_triple.company_id, competitor_source=competitor_source),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        competitor_responses: dict[str, CompetitorResponse] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        return GetCompetitorsFromIdentifiersResp(
            results=competitor_responses, errors=list(id_triple_resp.errors.values())
        )
