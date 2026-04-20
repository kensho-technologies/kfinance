import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE, SPGI_TICKER
from kfinance.domains.companies.company_models import (
    AuditorEntry,
    Auditors,
    CompanyDescriptions,
    CompanyOtherNames,
    NativeName,
    prefix_company_id,
)
from kfinance.domains.companies.company_tools import (
    GetCompanyDescriptionFromIdentifiersResp,
    GetCompanyOtherNamesFromIdentifiersResp,
    GetCompanySummaryFromIdentifiersResp,
    GetFinancialAuditorsFromIdentifiersResp,
    GetInfoFromIdentifiersResp,
    fetch_company_other_names_from_company_id,
    fetch_company_summary_and_description_from_company_id,
    fetch_financial_auditors_from_company_id,
    fetch_info_from_company_id,
    get_company_other_names_from_identifiers,
    get_company_summary_or_description_from_identifiers,
    get_financial_auditors_from_identifiers,
    get_info_from_identifiers,
)


class TestGetCompanyInfo:
    spgi_info_resp = {"name": "S&P Global Inc.", "status": "Operating"}

    @pytest.fixture
    def add_spgi_info_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI company info."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}",
            json=self.spgi_info_resp,
        )

    @pytest.mark.asyncio
    async def test_fetch_info_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_info_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's company info (using SPGI's company id)
        THEN we get back SPGI's company info
        """

        resp = await fetch_info_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        assert resp == self.spgi_info_resp

    @pytest.mark.asyncio
    async def test_get_info_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_info_mock_resp: None
    ) -> None:
        """
        WHEN we fetch company info for SPGI and a non-existent company
        THEN we get back SPGI's company info and an error for the non-existent company
        """

        expected_resp = GetInfoFromIdentifiersResp(
            results={"SPGI": self.spgi_info_resp},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )
        expected_resp.results["SPGI"]["company_id"] = prefix_company_id(SPGI_ID_TRIPLE.company_id)
        expected_resp.results["SPGI"]["ticker"] = SPGI_TICKER

        resp = await get_info_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp


class TestGetCompanyOtherNames:
    spgi_other_names_resp = {
        "alternate_names": ["S&P Global", "S&P Global, Inc.", "S&P"],
        "historical_names": [
            "McGraw-Hill Publishing Company, Inc.",
            "The McGraw-Hill Companies, Inc.",
        ],
        "native_names": [
            {"name": "KLab Venture Partners 株式会社", "language": "Japanese"},
            {"name": "株式会社ANOBAKA", "language": "Japanese"},
        ],
    }

    spgi_other_names_model = CompanyOtherNames(
        alternate_names=["S&P Global", "S&P Global, Inc.", "S&P"],
        historical_names=[
            "McGraw-Hill Publishing Company, Inc.",
            "The McGraw-Hill Companies, Inc.",
        ],
        native_names=[
            NativeName(name="KLab Venture Partners 株式会社", language="Japanese"),
            NativeName(name="株式会社ANOBAKA", language="Japanese"),
        ],
    )

    @pytest.fixture
    def add_spgi_other_names_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI other names."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}/names",
            json=self.spgi_other_names_resp,
        )

    @pytest.mark.asyncio
    async def test_get_company_other_names(
        self, httpx_client: httpx.AsyncClient, add_spgi_other_names_mock_resp: None
    ) -> None:
        """
        WHEN we fetch SPGI other names  (using SPGI's company id)
        THEN we get back SPGI other names.
        """

        resp = await fetch_company_other_names_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        assert resp == self.spgi_other_names_model

    @pytest.mark.asyncio
    async def test_get_other_names_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_other_names_mock_resp: None
    ) -> None:
        """
        WHEN we fetch other names for SPGI and a non-existent company
        THEN we get back SPGI's other names and an error for the non-existent company
        """

        expected_resp = GetCompanyOtherNamesFromIdentifiersResp(
            identifier_results={"SPGI": self.spgi_other_names_model},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_company_other_names_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp


class TestGetCompanySummaryAndDescription:
    spgi_descriptions_resp = {
        "summary": "S&P Global Inc. (S&P Global), [short summary]",
        "description": "S&P Global Inc., [long description]",
    }
    spgi_descriptions_model = CompanyDescriptions(
        summary="S&P Global Inc. (S&P Global), [short summary]",
        description="S&P Global Inc., [long description]",
    )

    @pytest.fixture
    def add_spgi_descriptions_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI descriptions."""
        httpx_mock.add_response(
            method="GET",
            url=f"https://kfinance.kensho.com/api/v1/info/{SPGI_COMPANY_ID}/descriptions",
            json=self.spgi_descriptions_resp,
        )

    @pytest.mark.asyncio
    async def test_fetch_company_summary_and_description_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_descriptions_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's summary and description (using SPGI's company id)
        THEN we get back SPGI's summary and description
        """

        resp = await fetch_company_summary_and_description_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        assert resp == self.spgi_descriptions_model

    @pytest.mark.asyncio
    async def test_get_company_summary_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_descriptions_mock_resp: None
    ) -> None:
        """
        WHEN we fetch the summary for SPGI and a non-existent company
        THEN we get back SPGI's summary and an error for the non-existent company
        """

        expected_resp = GetCompanySummaryFromIdentifiersResp(
            identifier_results={"SPGI": self.spgi_descriptions_model.summary},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_company_summary_or_description_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
            summary_or_description="summary",
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_get_company_description_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_descriptions_mock_resp: None
    ) -> None:
        """
        WHEN we fetch the description for SPGI and a non-existent company
        THEN we get back SPGI's description and an error for the non-existent company
        """

        expected_resp = GetCompanyDescriptionFromIdentifiersResp(
            identifier_results={"SPGI": self.spgi_descriptions_model.description},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_company_summary_or_description_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
            summary_or_description="description",
        )

        assert resp == expected_resp


class TestGetFinancialAuditors:
    spgi_auditors_api_resp = {
        "results": {
            str(SPGI_COMPANY_ID): {
                "CY2025/FY2025": [
                    {"auditor_company_id": "97518", "auditor_name": "Ernst & Young LLP"}
                ],
                "CY2024/FY2024": [
                    {"auditor_company_id": "97518", "auditor_name": "Ernst & Young LLP"}
                ],
            }
        },
        "errors": {},
    }

    spgi_auditors_model = Auditors(
        auditors_by_period={
            "CY2025/FY2025": [
                AuditorEntry(auditor_company_id=97518, auditor_name="Ernst & Young LLP")
            ],
            "CY2024/FY2024": [
                AuditorEntry(auditor_company_id=97518, auditor_name="Ernst & Young LLP")
            ],
        }
    )

    @pytest.fixture
    def add_spgi_auditors_mock_resp(self, httpx_mock: HTTPXMock) -> None:
        """Add mock response for SPGI financial auditors."""
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/auditors/",
            json=self.spgi_auditors_api_resp,
        )

    @pytest.mark.asyncio
    async def test_fetch_financial_auditors_from_company_id(
        self, httpx_client: httpx.AsyncClient, add_spgi_auditors_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's financial auditors (using SPGI's company id)
        THEN we get back SPGI's auditors grouped by period
        """

        resp = await fetch_financial_auditors_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        assert resp == self.spgi_auditors_model

    @pytest.mark.asyncio
    async def test_fetch_financial_auditors_with_year_range(
        self, httpx_client: httpx.AsyncClient, add_spgi_auditors_mock_resp: None
    ) -> None:
        """
        WHEN we request SPGI's financial auditors with start_year and end_year
        THEN we get back SPGI's auditors grouped by period
        """

        resp = await fetch_financial_auditors_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
            start_year=2024,
            end_year=2025,
        )

        assert resp == self.spgi_auditors_model

    @pytest.mark.asyncio
    async def test_get_financial_auditors_from_identifiers(
        self, httpx_client: httpx.AsyncClient, add_spgi_auditors_mock_resp: None
    ) -> None:
        """
        WHEN we fetch financial auditors for SPGI and a non-existent company
        THEN we get back SPGI's auditors and an error for the non-existent company
        """

        expected_resp = GetFinancialAuditorsFromIdentifiersResp(
            identifier_results={"SPGI": self.spgi_auditors_model},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[
                "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
            ],
        )

        resp = await get_financial_auditors_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
        )

        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_fetch_financial_auditors_empty_results(
        self, httpx_client: httpx.AsyncClient, httpx_mock: HTTPXMock
    ) -> None:
        """
        WHEN the API returns empty results for a company
        THEN we get back an Auditors model with an empty auditors_by_period dict
        """
        httpx_mock.add_response(
            method="POST",
            url="https://kfinance.kensho.com/api/v1/auditors/",
            json={"results": {}, "errors": {}},
        )

        resp = await fetch_financial_auditors_from_company_id(
            company_id=SPGI_ID_TRIPLE.company_id,
            httpx_client=httpx_client,
        )

        assert resp == Auditors(auditors_by_period={})
