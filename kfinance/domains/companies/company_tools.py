from textwrap import dedent
from typing import Literal, Type, overload

import httpx
from pydantic import BaseModel

from kfinance.async_batch_execution import AsyncTask, batch_execute_async_tasks
from kfinance.client.id_resolution import unified_fetch_id_triples
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_models import (
    CompanyDescriptions,
    CompanyOtherNames,
    prefix_company_id,
)
from kfinance.integrations.tool_calling.tool_calling_models import (
    KfinanceTool,
    ToolArgsWithIdentifiers,
    ToolRespWithErrors,
)


class GetInfoFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, dict]


class GetInfoFromIdentifiers(KfinanceTool):
    name: str = "get_info_from_identifiers"
    description: str = dedent("""
        Get the information associated with a list of identifiers. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, HQ country iso code, and CIQ company_id.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "What's the company information for Northrop Grumman and Lockheed Martin?"
        Function: get_info_from_identifiers(identifiers=["Northrop Grumman", "Lockheed Martin"])

        Query: "Get company info for UBER and LYFT"
        Function: get_info_from_identifiers(identifiers=["UBER", "LYFT"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    async def _arun(self, identifiers: list[str]) -> GetInfoFromIdentifiersResp:
        """"""
        return await get_info_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetCompanyOtherNamesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, CompanyOtherNames]


class GetCompanyOtherNamesFromIdentifiers(KfinanceTool):
    name: str = "get_company_other_names_from_identifiers"
    description: str = dedent("""
        Given a list of identifiers, fetch the alternate, historical, and native names associated with each identifier. Alternate names are additional names a company might go by (for example, Hewlett-Packard Company also goes by the name HP). Historical names are previous names for the company if it has changed over time. Native names are primary non-Latin character native names for global companies, including languages such as Arabic, Russian, Greek, Japanese, etc. This also includes limited history on native name changes.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "What are the alternate names for Meta and Alphabet?"
        Function: get_company_other_names_from_identifiers(identifiers=["Meta", "Alphabet"])

        Query: "Get other names for NSRGY"
        Function: get_company_other_names_from_identifiers(identifiers=["NSRGY"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.CompanyIntelligencePermission}

    async def _arun(
        self,
        identifiers: list[str],
    ) -> GetCompanyOtherNamesFromIdentifiersResp:
        """"""
        return await get_company_other_names_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
        )


class GetCompanySummaryFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, str]


class GetCompanySummaryFromIdentifiers(KfinanceTool):
    name: str = "get_company_summary_from_identifiers"
    description: str = dedent("""
        Get one paragraph summary/short descriptions of companies, including information about the company's primary business, products and services offered and their applications, business segment details, client/customer groups served, geographic markets served, distribution channels, strategic alliances/partnerships, founded/incorporated year, latest former name, and headquarters and additional offices.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "Give me summaries of Tesla and General Motors"
        Function: get_company_summary_from_identifiers(identifiers=["Tesla", "General Motors"])

        Query: "What are the summaries for F and STLA?"
        Function: get_company_summary_from_identifiers(identifiers=["F", "STLA"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.CompanyIntelligencePermission}

    async def _arun(
        self,
        identifiers: list[str],
    ) -> GetCompanySummaryFromIdentifiersResp:
        """"""
        return await get_company_summary_or_description_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            summary_or_description="summary",
        )


class GetCompanyDescriptionFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, str]


class GetCompanyDescriptionFromIdentifiers(KfinanceTool):
    name: str = "get_company_description_from_identifiers"
    description: str = dedent("""
        Get detailed descriptions of companies, broken down into sections, which may include information about the company's Primary business, Segments (including Products and Services for each), Competition, Significant events, and History. Within the text, four spaces represent a new paragraph. Note that the description is divided into sections with headers, where each section has a new paragraph (four spaces) before and after the section header.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.

        Examples:
        Query: "Get detailed descriptions for Netflix and Disney"
        Function: get_company_description_from_identifiers(identifiers=["Netflix", "Disney"])

        Query: "What are the detailed company descriptions for KO and PEP?"
        Function: get_company_description_from_identifiers(identifiers=["KO", "PEP"])
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.CompanyIntelligencePermission}

    async def _arun(
        self,
        identifiers: list[str],
    ) -> GetCompanyDescriptionFromIdentifiersResp:
        """"""
        return await get_company_summary_or_description_from_identifiers(
            identifiers=identifiers,
            httpx_client=self.kfinance_client.httpx_client,
            summary_or_description="description",
        )


async def get_info_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetInfoFromIdentifiersResp:
    """Fetch company info from identifiers

    Sample response:

        {   "results": {
                "SPGI": {
                    "name": "S&P Global Inc.",
                    "status": "Operating",
                    "type": "Public Company",
                    "simple_industry": "Capital Markets",
                    "number_of_employees": "42350.0000",
                    "founding_date": "1860-01-01",
                    "webpage": "www.spglobal.com",
                    "address": "55 Water Street",
                    "city": "New York",
                    "zip_code": "10041-0001",
                    "state": "New York",
                    "country": "United States",
                    "iso_country": "USA",
                    "company_id": "C_21719"
                }
            },
            "errors": [['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
    """

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_info_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, dict[str, str]] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items():
        results[identifier]["company_id"] = prefix_company_id(id_triple.company_id)

    resp_model = GetInfoFromIdentifiersResp(results=results, errors=errors)
    return resp_model


async def fetch_info_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> dict[str, str]:
    """Fetch and return company info for one company_id."""
    url = f"/info/{company_id}"
    resp = await httpx_client.get(url=url)
    return resp.json()


async def get_company_other_names_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
) -> GetCompanyOtherNamesFromIdentifiersResp:
    """Fetch native, historical, and alternative names for all identifiers."""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_company_other_names_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, CompanyOtherNames] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            results[task.result_key] = task.result

    return GetCompanyOtherNamesFromIdentifiersResp(results=results, errors=errors)


async def fetch_company_other_names_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> CompanyOtherNames:
    """Fetch and return other names for one company_id."""
    url = f"/info/{company_id}/names"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return CompanyOtherNames.model_validate(resp.json())


@overload
async def get_company_summary_or_description_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    summary_or_description: Literal["summary"],
) -> GetCompanySummaryFromIdentifiersResp: ...


@overload
async def get_company_summary_or_description_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    summary_or_description: Literal["description"],
) -> GetCompanyDescriptionFromIdentifiersResp: ...


async def get_company_summary_or_description_from_identifiers(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    summary_or_description: Literal["summary", "description"],
) -> GetCompanySummaryFromIdentifiersResp | GetCompanyDescriptionFromIdentifiersResp:
    """Return either the short company summary or the long company description for each identifier"""

    id_triple_resp = await unified_fetch_id_triples(
        identifiers=identifiers, httpx_client=httpx_client
    )
    errors: list[str] = list(id_triple_resp.errors.values())

    tasks = [
        AsyncTask(
            func=fetch_company_summary_and_description_from_company_id,
            kwargs=dict(
                company_id=id_triple.company_id,
                httpx_client=httpx_client,
            ),
            result_key=identifier,
        )
        for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
    ]

    await batch_execute_async_tasks(tasks=tasks)

    results: dict[str, str] = dict()
    for task in tasks:
        if task.error:
            errors.append(task.error)
        else:
            if summary_or_description == "summary":
                result = task.result.summary
            else:
                result = task.result.description
            results[task.result_key] = result

    if summary_or_description == "summary":
        return GetCompanySummaryFromIdentifiersResp(results=results, errors=errors)
    else:
        return GetCompanyDescriptionFromIdentifiersResp(results=results, errors=errors)


async def fetch_company_summary_and_description_from_company_id(
    company_id: int,
    httpx_client: httpx.AsyncClient,
) -> CompanyDescriptions:
    """Fetch the short company summary and long description for a company id."""
    url = f"/info/{company_id}/descriptions"
    resp = await httpx_client.get(url=url)
    resp.raise_for_status()
    return CompanyDescriptions.model_validate(resp.json())
