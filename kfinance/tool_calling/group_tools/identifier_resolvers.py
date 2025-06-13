from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.fetch import KFinanceApiClient
from kfinance.tool_calling.group_tools.company_identifiers import CompanyIdentifier


def fetch_company_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:

    tasks = [
        Task(func=identifier.fetch_company_id, result_key=identifier, kwargs=dict(api_client=api_client))
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(
        api_client=api_client, tasks=tasks
    )


def fetch_security_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:
    tasks = [
        Task(func=identifier.fetch_security_id, result_key=identifier, kwargs=dict(api_client=api_client))
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(
        api_client=api_client, tasks=tasks
    )

def fetch_trading_item_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:
    tasks = [
        Task(func=identifier.fetch_trading_item_id, result_key=identifier, kwargs=dict(api_client=api_client))
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(
        api_client=api_client, tasks=tasks
    )
