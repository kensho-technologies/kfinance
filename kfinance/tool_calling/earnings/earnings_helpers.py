from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.fetch import KFinanceApiClient
from kfinance.models.earnings_models import EarningsCallResp
from kfinance.tool_calling.company_identifiers import CompanyId, CompanyIdentifier, parse_identifiers, \
    fetch_company_ids_from_identifiers


def get_earnings_from_identifiers(identifiers: list[str], kfinance_api_client: KFinanceApiClient) -> dict[CompanyIdentifier, EarningsCallResp]:
    """Return the earnings call response for all passed identifiers."""

    parsed_identifiers = parse_identifiers(identifiers)
    identifiers_to_company_ids = fetch_company_ids_from_identifiers(
        identifiers=parsed_identifiers, api_client=kfinance_api_client
    )

    tasks = [
        Task(
            func=kfinance_api_client.fetch_earnings,
            kwargs=dict(company_id=company_id),
            result_key=identifier,
        )
        for identifier, company_id in identifiers_to_company_ids.items()
    ]

    earnings_responses = process_tasks_in_thread_pool_executor(
        api_client=kfinance_api_client, tasks=tasks
    )
    return earnings_responses