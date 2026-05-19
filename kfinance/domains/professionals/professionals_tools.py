from textwrap import dedent
from typing import Type

import httpx
from pydantic import BaseModel, Field

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.professionals.professionals_models import (
    CompanyProfessional,
    CompanyProfessionalsResp,
    PersonProfessionalsResp,
    PersonProfessionalsResult,
    ProfessionalType,
    Timeframe,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
    ToolRespWithIdInfoAndErrors,
)


class GetProfessionalsFromIdentifiersArgs(ToolArgsWithIdentifiers):
    professional_type: ProfessionalType = Field(
        description="Filter by professional type: 'board_members' or 'employees'.",
    )
    timeframe: Timeframe = Field(
        default=Timeframe.all,
        description="Filter by timeframe: 'all', 'current', or 'prior'.",
    )
    include_compensation: bool = Field(
        default=False,
        description="Whether to include compensation data in the response. Defaults to False.",
    )


class GetProfessionalsFromIdentifiersResp(
    ToolRespWithIdInfoAndErrors[dict[str, list[CompanyProfessional]]]
):
    pass


class GetProfessionalsFromIdentifiers(KfinanceTool):
    name: str = "get_professionals_from_identifiers"
    description: str = dedent("""
        Get the professionals (board members and/or employees) associated with a list of companies.

        Returns professionals grouped by function name for each identifier, including
        person_id, name, title, professional types, tenure dates, and compensation.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
        - Use professional_type to restrict to 'board_members' or 'employees'.
        - Use timeframe to filter by 'current', 'prior', or 'all' professionals.

        Examples:
        Query: "Who are the current board members of Apple?"
        Function: get_professionals_from_identifiers(identifiers=["Apple"], professional_type="board_members", timeframe="current")

        Query: "Get all current employees for S&P Global and Meta"
        Function: get_professionals_from_identifiers(identifiers=["SPGI", "META"], professional_type="employees", timeframe="current")

        Query: "Who were the past employees of Netflix?"
        Function: get_professionals_from_identifiers(identifiers=["Netflix"], professional_type="employees", timeframe="prior")

        Query: "Who are the current board members of Apple, including compensation details?"
        Function: get_professionals_from_identifiers(identifiers=["Apple"], professional_type="board_members", timeframe="current", include_compensation=True)
    """).strip()
    args_schema: Type[BaseModel] = GetProfessionalsFromIdentifiersArgs
    accepted_permissions: set[Permission] | None = {Permission.ProfessionalsPermission}

    async def _arun(
        self,
        identifiers: list[str],
        professional_type: ProfessionalType,
        timeframe: Timeframe = Timeframe.all,
        include_compensation: bool = False,
    ) -> GetProfessionalsFromIdentifiersResp:
        return await get_professionals_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            professional_type=professional_type,
            timeframe=timeframe,
            include_compensation=include_compensation,
        )


class GetProfessionalsFromPersonIdsArgs(BaseModel):
    person_ids: list[int] = Field(
        min_length=1,
        description="List of person_ids to look up professional history for.",
    )
    include_compensation: bool = Field(
        default=False,
        description="Whether to include compensation data in the response. Defaults to False.",
    )
    include_biography: bool = Field(
        default=False,
        description="Whether to include biography in the response. Defaults to False.",
    )


class GetProfessionalsFromPersonIdsResp(ToolRespWithErrors):
    results: dict[str, PersonProfessionalsResult] = Field(default_factory=dict)


class GetProfessionalsFromPersonIds(KfinanceTool):
    name: str = "get_professionals_from_person_ids"
    description: str = dedent("""
        Get the professional history for one or more people by their person_id.

        Returns each person's name, biography, and full role history across all companies,
        including title, tenure dates, professional types, and compensation.

        - person_id values can be obtained from get_professionals_from_identifiers results.
        - When possible, pass multiple person_ids in a single call rather than making multiple calls.

        Examples:
        Query: "Tell me about Tim Cook's career history"
        Function: get_professionals_from_person_ids(person_ids=[169600])

        Query: "Get career histories for person_ids 169600 and 12345"
        Function: get_professionals_from_person_ids(person_ids=[169600, 12345])

        Query: "Get Tim Cook's career history including biography and compensation"
        Function: get_professionals_from_person_ids(person_ids=[169600], include_compensation=True, include_biography=True)
    """).strip()
    args_schema: Type[BaseModel] = GetProfessionalsFromPersonIdsArgs
    accepted_permissions: set[Permission] | None = {Permission.ProfessionalsPermission}

    async def _arun(
        self,
        person_ids: list[int],
        include_compensation: bool = False,
        include_biography: bool = False,
    ) -> GetProfessionalsFromPersonIdsResp:
        return await get_professionals_from_person_ids(
            person_ids=person_ids,
            httpx_client=self.kfinance_client.httpx_client,
            include_compensation=include_compensation,
            include_biography=include_biography,
        )


async def get_professionals_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    professional_type: ProfessionalType,
    timeframe: Timeframe = Timeframe.all,
    include_compensation: bool = False,
) -> GetProfessionalsFromIdentifiersResp:
    """Fetch company professionals for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_professionals_company,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
                professional_type=professional_type,
                timeframe=timeframe,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, dict[str, list[CompanyProfessional]]] = {}
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            company_resp: CompanyProfessionalsResp = task.result
            results[task.result_key] = company_resp.results.get(str(task.kwargs["company_id"]), {})

    if not include_compensation:
        for func_professionals in results.values():
            for professionals in func_professionals.values():
                for professional in professionals:
                    professional.compensation = None

    return GetProfessionalsFromIdentifiersResp(
        identifier_results=results,
        identifier_info=id_triple_resp.identifiers_to_id_triples,
        errors=errors,
    )


async def get_professionals_from_person_ids(
    person_ids: list[int],
    httpx_client: httpx.AsyncClient,
    include_compensation: bool = False,
    include_biography: bool = False,
) -> GetProfessionalsFromPersonIdsResp:
    """Fetch professional history for all person_ids."""
    tasks = [
        AsyncTask(
            func=fetch_professionals_person,
            kwargs=dict(person_id=person_id, httpx_client=httpx_client),
            result_key=str(person_id),
        )
        for person_id in person_ids
    ]

    await batch_execute_async_tasks(tasks=tasks)

    errors: list[str] = []
    results: dict[str, PersonProfessionalsResult] = {}
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            person_resp: PersonProfessionalsResp = task.result
            results.update(person_resp.results)

    if not include_biography:
        for person in results.values():
            person.biography = None

    if not include_compensation:
        for person in results.values():
            for func_roles in person.roles.values():
                for roles in func_roles.values():
                    for role in roles:
                        role.compensation = None

    return GetProfessionalsFromPersonIdsResp(results=results, errors=errors)


async def fetch_professionals_company(
    company_id: int,
    httpx_client: httpx.AsyncClient,
    professional_type: ProfessionalType,
    timeframe: Timeframe = Timeframe.all,
) -> CompanyProfessionalsResp:
    """Fetch professionals for one company_id."""
    url = f"/professionals/company/{company_id}/{professional_type}/{timeframe}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return CompanyProfessionalsResp.model_validate(resp.json())


async def fetch_professionals_person(
    person_id: int,
    httpx_client: httpx.AsyncClient,
) -> PersonProfessionalsResp:
    """Fetch professional history for one person_id."""
    url = f"/professionals/person/{person_id}"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return PersonProfessionalsResp.model_validate(resp.json())
