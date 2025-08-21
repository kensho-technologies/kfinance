from textwrap import dedent
from typing import Type

from pydantic import BaseModel

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.permission_models import Permission
from kfinance.domains.companies.company_models import CompanyDescriptions, CompanyOtherNames
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
        Get the information associated with a list of identifiers. Info includes company name, status, type, simple industry, number of employees (if available), founding date, webpage, HQ address, HQ city, HQ zip code, HQ state, HQ country, and HQ country iso code.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = None

    def _run(self, identifiers: list[str]) -> GetInfoFromIdentifiersResp:
        """Sample response:

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
                    "iso_country": "USA"
                }
            },
            "errors": [['No identification triple found for the provided identifier: NON-EXISTENT of type: ticker']
        }
        """
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_info,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]

        info_responses: dict[str, dict] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        return GetInfoFromIdentifiersResp(
            results=info_responses, errors=list(id_triple_resp.errors.values())
        )


class GetCompanyOtherNamesFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, CompanyOtherNames]


class GetCompanyOtherNamesFromIdentifiers(KfinanceTool):
    name: str = "get_company_other_names_from_identifiers"
    description: str = dedent("""
        Given a list of identifiers, fetch the alternate, historical, and native names associated with each identifier. Alternate names are additional names a company might go by (for example, Hewlett-Packard Company also goes by the name HP). Historical names are previous names for the company if it has changed over time. Native names are primary non-Latin character native names for global companies, including languages such as Arabic, Russian, Greek, Japanese, etc. This also includes limited history on native name changes.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.CompanyIntelligencePermission}

    def _run(
        self,
        identifiers: list[str],
    ) -> GetCompanyOtherNamesFromIdentifiersResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)
        tasks = [
            Task(
                func=api_client.fetch_company_other_names,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]
        info_responses: dict[str, CompanyOtherNames] = process_tasks_in_thread_pool_executor(
            api_client=api_client, tasks=tasks
        )
        return GetCompanyOtherNamesFromIdentifiersResp(
            results=info_responses, errors=list(id_triple_resp.errors.values())
        )


class GetCompanySummaryFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, str]


class GetCompanySummaryFromIdentifiers(KfinanceTool):
    name: str = "get_company_summary_from_identifiers"
    description: str = dedent("""
        Get one paragraph summary/short descriptions of companies, including information about the company's primary business, products and services offered and their applications, business segment details, client/customer groups served, geographic markets served, distribution channels, strategic alliances/partnerships, founded/incorporated year, latest former name, and headquarters and additional offices."

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.CompanyIntelligencePermission}

    def _run(
        self,
        identifiers: list[str],
    ) -> GetCompanySummaryFromIdentifiersResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_company_descriptions,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]
        company_description_responses: dict[str, CompanyDescriptions] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )

        # Extract only the summary field
        summary_results = {
            identifier: descriptions.summary
            for identifier, descriptions in company_description_responses.items()
        }

        return GetCompanySummaryFromIdentifiersResp(
            results=summary_results, errors=list(id_triple_resp.errors.values())
        )


class GetCompanyDescriptionFromIdentifiersResp(ToolRespWithErrors):
    results: dict[str, str]


class GetCompanyDescriptionFromIdentifiers(KfinanceTool):
    name: str = "get_company_description_from_identifiers"
    description: str = dedent("""
        Get detailed descriptions of companies, broken down into sections, which may include information about the company's Primary business, Segments (including Products and Services for each), Competition, Significant events, and History. Within the text, four spaces represent a new paragraph. Note that the description is divided into sections with headers, where each section has a new paragraph (four spaces) before and after the section header.

        - When possible, pass multiple identifiers in a single call rather than making multiple calls.
    """).strip()
    args_schema: Type[BaseModel] = ToolArgsWithIdentifiers
    accepted_permissions: set[Permission] | None = {Permission.CompanyIntelligencePermission}

    def _run(
        self,
        identifiers: list[str],
    ) -> GetCompanyDescriptionFromIdentifiersResp:
        api_client = self.kfinance_client.kfinance_api_client
        id_triple_resp = api_client.unified_fetch_id_triples(identifiers=identifiers)

        tasks = [
            Task(
                func=api_client.fetch_company_descriptions,
                kwargs=dict(company_id=id_triple.company_id),
                result_key=identifier,
            )
            for identifier, id_triple in id_triple_resp.identifiers_to_id_triples.items()
        ]
        company_description_responses: dict[str, CompanyDescriptions] = (
            process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
        )

        # Extract only the description field
        description_results = {
            identifier: descriptions.description
            for identifier, descriptions in company_description_responses.items()
        }

        return GetCompanyDescriptionFromIdentifiersResp(
            results=description_results, errors=list(id_triple_resp.errors.values())
        )
