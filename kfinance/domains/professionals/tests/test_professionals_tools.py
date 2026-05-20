import httpx
import pytest
from pytest_httpx import HTTPXMock

from kfinance.conftest import SPGI_COMPANY_ID, SPGI_ID_TRIPLE
from kfinance.domains.professionals.professionals_models import (
    CompanyProfessional,
    CompanyProfessionalsResp,
    PersonProfessionalsResp,
    PersonProfessionalsResult,
    PersonRole,
    ProfessionalType,
    Timeframe,
)
from kfinance.domains.professionals.professionals_tools import (
    GetProfessionalsFromIdentifiersResp,
    fetch_professionals_company,
    fetch_professionals_person,
    get_professionals_from_identifiers,
    get_professionals_from_person_ids,
)


SPGI_BOARD_MEMBER = CompanyProfessional(
    person_id=12345,
    first_name="Jane",
    last_name="Doe",
    title="Independent Director",
    professional_types=["board_members"],
    start_date="2015-01-01",
    end_date=None,
    is_current=True,
)

SPGI_EMPLOYEE = CompanyProfessional(
    person_id=67890,
    first_name="John",
    last_name="Smith",
    title="Chief Executive Officer",
    professional_types=["employees"],
    start_date="2013-11-01",
    end_date=None,
    is_current=True,
    compensation={"2023": {"Annual Base Salary": 1000000.0}},
)

MOCK_BOARD_RESP = CompanyProfessionalsResp(
    results={str(SPGI_COMPANY_ID): {"Independent Director": [SPGI_BOARD_MEMBER]}},
    errors={},
)

MOCK_EMPLOYEE_RESP = CompanyProfessionalsResp(
    results={str(SPGI_COMPANY_ID): {"Chief Executive Officer": [SPGI_EMPLOYEE]}},
    errors={},
)

SPGI_CEO_PERSON_ID = 67890

SPGI_CEO_ROLE = PersonRole(
    company_name="S&P Global Inc.",
    title="Chief Executive Officer",
    start_date="2013-11-01",
    end_date=None,
    is_current=True,
    professional_types=["employees"],
    compensation={"2023": {"Annual Base Salary": 1000000.0}},
)

MOCK_PERSON_RESP = PersonProfessionalsResp(
    results={
        str(SPGI_CEO_PERSON_ID): PersonProfessionalsResult(
            first_name="John",
            last_name="Smith",
            biography="John Smith is the CEO of S&P Global Inc.",
            roles={str(SPGI_COMPANY_ID): {"Chief Executive Officer": [SPGI_CEO_ROLE]}},
        )
    },
    errors={},
)


@pytest.fixture
def add_spgi_board_mock_resp(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/professionals/company/{SPGI_COMPANY_ID}/board_members/all",
        json=MOCK_BOARD_RESP.model_dump(mode="json"),
        is_reusable=True,
    )


@pytest.fixture
def add_spgi_employee_mock_resp(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/professionals/company/{SPGI_COMPANY_ID}/employees/current",
        json=MOCK_EMPLOYEE_RESP.model_dump(mode="json"),
        is_reusable=True,
    )


@pytest.fixture
def add_spgi_past_employee_mock_resp(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/professionals/company/{SPGI_COMPANY_ID}/employees/prior",
        json=MOCK_EMPLOYEE_RESP.model_dump(mode="json"),
        is_reusable=True,
    )


@pytest.fixture
def add_spgi_person_mock_resp(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"https://kfinance.kensho.com/api/v1/professionals/person/{SPGI_CEO_PERSON_ID}",
        json=MOCK_PERSON_RESP.model_dump(mode="json"),
        is_reusable=True,
    )


class TestBuildName:
    def test_first_and_last_name(self) -> None:
        """
        WHEN only first and last name are provided
        THEN name is "{first} {last}".
        """
        p = CompanyProfessional(person_id=1, first_name="Jane", last_name="Doe")
        assert p.name == "Jane Doe"

    def test_first_middle_last(self) -> None:
        """
        WHEN first, middle, and last name are provided
        THEN name includes all three.
        """
        p = CompanyProfessional(
            person_id=1, first_name="Jane", middle_name="Marie", last_name="Doe"
        )
        assert p.name == "Jane Marie Doe"

    def test_salutation_is_quoted(self) -> None:
        """
        WHEN a salutation is provided
        THEN it is wrapped in quotes between middle and last name.
        """
        p = CompanyProfessional(
            person_id=1, first_name="Jane", salutation="Jimmy", last_name="Doe"
        )
        assert p.name == 'Jane "Jimmy" Doe'

    def test_suffix(self) -> None:
        """
        WHEN a suffix is provided
        THEN it appears at the end of the name.
        """
        p = CompanyProfessional(person_id=1, first_name="Jane", last_name="Doe", suffix="Jr.")
        assert p.name == "Jane Doe Jr."

    def test_all_parts(self) -> None:
        """
        WHEN all name parts are provided
        THEN name follows [First] [Middle] "[Salutation]" [Last] [Suffix] format.
        """
        p = CompanyProfessional(
            person_id=1,
            first_name="Jane",
            middle_name="Marie",
            salutation="Jimmy",
            last_name="Doe",
            suffix="Jr.",
        )
        assert p.name == 'Jane Marie "Jimmy" Doe Jr.'

    def test_none_parts_are_skipped(self) -> None:
        """
        WHEN some name parts are None
        THEN only present parts appear in name.
        """
        p = CompanyProfessional(person_id=1, first_name="Jane", last_name="Doe", suffix=None)
        assert p.name == "Jane Doe"

    def test_all_parts_none_gives_none_name(self) -> None:
        """
        WHEN no name parts are provided
        THEN name is None.
        """
        p = CompanyProfessional(person_id=1)
        assert p.name is None

    def test_existing_name_not_overwritten(self) -> None:
        """
        WHEN name is explicitly provided along with individual parts
        THEN the explicit name is preserved.
        """
        p = CompanyProfessional(
            person_id=1, name="Custom Name", first_name="Jane", last_name="Doe"
        )
        assert p.name == "Custom Name"

    def test_prefix_is_separate_from_name(self) -> None:
        """
        WHEN prefix is provided
        THEN it is stored as a separate field and not included in name.
        """
        p = CompanyProfessional(
            person_id=1, prefix="Dr.", first_name="Jane", last_name="Doe"
        )
        assert p.name == "Jane Doe"
        assert p.prefix == "Dr."

    def test_person_professionals_result_build_name(self) -> None:
        """
        WHEN building a PersonProfessionalsResult with individual name parts
        THEN name is assembled the same way.
        """
        p = PersonProfessionalsResult(
            first_name="John",
            middle_name="William",
            salutation="Johnny",
            last_name="Smith",
            suffix="III",
        )
        assert p.name == 'John William "Johnny" Smith III'

    def test_person_professionals_result_prefix_is_separate(self) -> None:
        """
        WHEN a PersonProfessionalsResult has a prefix
        THEN prefix is stored separately and not part of name.
        """
        p = PersonProfessionalsResult(prefix="Dr.", first_name="John", last_name="Smith")
        assert p.name == "John Smith"
        assert p.prefix == "Dr."


class TestFetchProfessionalsCompany:
    @pytest.mark.asyncio
    async def test_fetch_board_members(
        self, httpx_client: httpx.AsyncClient, add_spgi_board_mock_resp: None
    ) -> None:
        """
        WHEN we fetch SPGI's board members using SPGI's company id
        THEN we get back a CompanyProfessionalsResp with SPGI's board members.
        """
        resp = await fetch_professionals_company(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            professional_type=ProfessionalType.board_members,
            timeframe=Timeframe.all,
        )
        assert resp == MOCK_BOARD_RESP

    @pytest.mark.asyncio
    async def test_fetch_current_employees(
        self, httpx_client: httpx.AsyncClient, add_spgi_employee_mock_resp: None
    ) -> None:
        """
        WHEN we fetch SPGI's current employees using SPGI's company id
        THEN we get back a CompanyProfessionalsResp with SPGI's current employees.
        """
        resp = await fetch_professionals_company(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            professional_type=ProfessionalType.employees,
            timeframe=Timeframe.current,
        )
        assert resp == MOCK_EMPLOYEE_RESP

    @pytest.mark.asyncio
    async def test_fetch_past_employees(
        self, httpx_client: httpx.AsyncClient, add_spgi_past_employee_mock_resp: None
    ) -> None:
        """
        WHEN we fetch SPGI's past employees using SPGI's company id
        THEN we get back a CompanyProfessionalsResp with SPGI's past employees.
        """
        resp = await fetch_professionals_company(
            company_id=SPGI_COMPANY_ID,
            httpx_client=httpx_client,
            professional_type=ProfessionalType.employees,
            timeframe=Timeframe.prior,
        )
        assert resp == MOCK_EMPLOYEE_RESP


class TestFetchProfessionalsPerson:
    @pytest.mark.asyncio
    async def test_fetch_person_professionals(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch professional history for a person using their person_id
        THEN we get back a PersonProfessionalsResp with their roles.
        """
        resp = await fetch_professionals_person(
            person_id=SPGI_CEO_PERSON_ID,
            httpx_client=httpx_client,
        )
        assert resp == MOCK_PERSON_RESP

    @pytest.mark.asyncio
    async def test_fetch_person_roles_structure(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch professional history for a person
        THEN the response contains roles keyed by company_id then function name.
        """
        resp = await fetch_professionals_person(
            person_id=SPGI_CEO_PERSON_ID,
            httpx_client=httpx_client,
        )
        person = resp.results[str(SPGI_CEO_PERSON_ID)]
        assert person.name == "John Smith"
        company_roles = person.roles[str(SPGI_COMPANY_ID)]
        ceo_roles = company_roles["Chief Executive Officer"]
        assert len(ceo_roles) == 1
        assert ceo_roles[0].company_name == "S&P Global Inc."
        assert ceo_roles[0].is_current is True


class TestGetProfessionalsFromIdentifiers:
    @pytest.mark.asyncio
    async def test_get_board_members(
        self, httpx_client: httpx.AsyncClient, add_spgi_board_mock_resp: None
    ) -> None:
        """
        WHEN we fetch board members for SPGI by identifier
        THEN we get back SPGI's board members keyed by identifier.
        """
        expected_resp = GetProfessionalsFromIdentifiersResp(
            identifier_results={"SPGI": {"Independent Director": [SPGI_BOARD_MEMBER]}},
            identifier_info={"SPGI": SPGI_ID_TRIPLE},
            errors=[],
        )
        resp = await get_professionals_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            professional_type=ProfessionalType.board_members,
            timeframe=Timeframe.all,
        )
        assert resp == expected_resp

    @pytest.mark.asyncio
    async def test_include_compensation_false_strips_compensation(
        self, httpx_client: httpx.AsyncClient, add_spgi_employee_mock_resp: None
    ) -> None:
        """
        WHEN we fetch employees with include_compensation=False
        THEN compensation is stripped from all professionals.
        """
        resp = await get_professionals_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            professional_type=ProfessionalType.employees,
            timeframe=Timeframe.current,
            include_compensation=False,
        )
        for func_professionals in resp.identifier_results.values():
            for professionals in func_professionals.values():
                for professional in professionals:
                    assert professional.compensation is None

    @pytest.mark.asyncio
    async def test_include_compensation_true_keeps_compensation(
        self, httpx_client: httpx.AsyncClient, add_spgi_employee_mock_resp: None
    ) -> None:
        """
        WHEN we fetch employees with include_compensation=True
        THEN compensation is included in the response.
        """
        resp = await get_professionals_from_identifiers(
            identifiers=["SPGI"],
            httpx_client=httpx_client,
            professional_type=ProfessionalType.employees,
            timeframe=Timeframe.current,
            include_compensation=True,
        )
        ceo = resp.identifier_results["SPGI"]["Chief Executive Officer"][0]
        assert ceo.compensation == {"2023": {"Annual Base Salary": 1000000.0}}

    @pytest.mark.asyncio
    async def test_get_professionals_with_invalid_identifier(
        self,
        httpx_client: httpx.AsyncClient,
        add_spgi_board_mock_resp: None,
    ) -> None:
        """
        WHEN we fetch professionals for SPGI and a non-existent identifier
        THEN we get back SPGI's professionals and an error for the non-existent identifier.
        """
        resp = await get_professionals_from_identifiers(
            identifiers=["SPGI", "non-existent"],
            httpx_client=httpx_client,
            professional_type=ProfessionalType.board_members,
            timeframe=Timeframe.all,
        )
        assert "SPGI" in resp.identifier_results
        assert len(resp.errors) == 1


class TestGetProfessionalsFromPersonIds:
    @pytest.mark.asyncio
    async def test_get_person_professionals(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch professional history for a person by person_id
        THEN we get back that person's result keyed by person_id string.
        """
        resp = await get_professionals_from_person_ids(
            person_ids=[SPGI_CEO_PERSON_ID],
            httpx_client=httpx_client,
        )
        assert resp.errors == []
        assert str(SPGI_CEO_PERSON_ID) in resp.results
        assert resp.results[str(SPGI_CEO_PERSON_ID)].name == "John Smith"

    @pytest.mark.asyncio
    async def test_get_multiple_persons(
        self,
        httpx_client: httpx.AsyncClient,
        httpx_mock: HTTPXMock,
        add_spgi_person_mock_resp: None,
    ) -> None:
        """
        WHEN we fetch professional history for multiple person_ids and one returns a 404
        THEN we get back results for the successful one and an error for the failed one.
        """
        httpx_mock.add_response(
            method="GET",
            url="https://kfinance.kensho.com/api/v1/professionals/person/99999",
            status_code=404,
        )
        resp = await get_professionals_from_person_ids(
            person_ids=[SPGI_CEO_PERSON_ID, 99999],
            httpx_client=httpx_client,
        )
        assert str(SPGI_CEO_PERSON_ID) in resp.results
        assert len(resp.errors) == 1

    @pytest.mark.asyncio
    async def test_include_biography_false_strips_biography(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch person professionals with include_biography=False
        THEN biography is stripped from all results.
        """
        resp = await get_professionals_from_person_ids(
            person_ids=[SPGI_CEO_PERSON_ID],
            httpx_client=httpx_client,
            include_biography=False,
        )
        assert resp.results[str(SPGI_CEO_PERSON_ID)].biography is None

    @pytest.mark.asyncio
    async def test_include_biography_true_keeps_biography(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch person professionals with include_biography=True
        THEN biography is included in the response.
        """
        resp = await get_professionals_from_person_ids(
            person_ids=[SPGI_CEO_PERSON_ID],
            httpx_client=httpx_client,
            include_biography=True,
        )
        assert (
            resp.results[str(SPGI_CEO_PERSON_ID)].biography
            == "John Smith is the CEO of S&P Global Inc."
        )

    @pytest.mark.asyncio
    async def test_include_compensation_false_strips_compensation(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch person professionals with include_compensation=False
        THEN compensation is stripped from all roles.
        """
        resp = await get_professionals_from_person_ids(
            person_ids=[SPGI_CEO_PERSON_ID],
            httpx_client=httpx_client,
            include_compensation=False,
        )
        person = resp.results[str(SPGI_CEO_PERSON_ID)]
        for func_roles in person.roles.values():
            for roles in func_roles.values():
                for role in roles:
                    assert role.compensation is None

    @pytest.mark.asyncio
    async def test_include_compensation_true_keeps_compensation(
        self, httpx_client: httpx.AsyncClient, add_spgi_person_mock_resp: None
    ) -> None:
        """
        WHEN we fetch person professionals with include_compensation=True
        THEN compensation is included in the response.
        """
        resp = await get_professionals_from_person_ids(
            person_ids=[SPGI_CEO_PERSON_ID],
            httpx_client=httpx_client,
            include_compensation=True,
        )
        person = resp.results[str(SPGI_CEO_PERSON_ID)]
        ceo_role = person.roles[str(SPGI_COMPANY_ID)]["Chief Executive Officer"][0]
        assert ceo_role.compensation == {"2023": {"Annual Base Salary": 1000000.0}}
