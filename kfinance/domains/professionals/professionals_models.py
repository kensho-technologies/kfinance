from typing import Any

from pydantic import BaseModel
from strenum import StrEnum


class ProfessionalType(StrEnum):
    board_members = "board_members"
    employees = "employees"


class Timeframe(StrEnum):
    all = "all"
    current = "current"
    prior = "prior"


class CompanyProfessional(BaseModel):
    prefix: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    suffix: str | None = None
    salutation: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    professional_types: list[str] = []
    person_id: int
    # keyed by fiscal year (str), then by compensation type name
    compensation: dict[str, dict[str, Any]] = {}


class CompanyProfessionalsResp(BaseModel):
    # keyed by company_id (str) -> function name -> list of professionals
    results: dict[str, dict[str, list[CompanyProfessional]]]
    errors: dict[str, str] = {}


class PersonRole(BaseModel):
    company_name: str
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    professional_types: list[str] = []
    # keyed by fiscal year (str), then by compensation type name
    compensation: dict[str, dict[str, Any]] = {}


class PersonProfessionalsResult(BaseModel):
    prefix: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    suffix: str | None = None
    salutation: str | None = None
    biography: str | None = None
    # keyed by company_id (str) -> function name -> list of roles
    roles: dict[str, dict[str, list[PersonRole]]] = {}


class PersonProfessionalsResp(BaseModel):
    # keyed by person_id (str)
    results: dict[str, PersonProfessionalsResult]
    errors: dict[str, str] = {}
