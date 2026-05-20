from typing import Any

from pydantic import BaseModel, model_validator
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
    name: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    professional_types: list[str] = []
    person_id: int
    # keyed by fiscal year (str), then by compensation type name
    compensation: dict[str, dict[str, Any]] | None = None

    @model_validator(mode="before")
    @classmethod
    def build_name(cls, data: Any) -> Any:
        """Build name from individual name parts in the format: First Middle "Salutation" Last Suffix."""
        if isinstance(data, dict) and not data.get("name"):
            salutation = data.get("salutation")
            parts = [
                data.get("first_name"),
                data.get("middle_name"),
                f'"{salutation}"' if salutation else None,
                data.get("last_name"),
                data.get("suffix"),
            ]
            filtered = [p for p in parts if p]
            if filtered:
                data["name"] = " ".join(filtered)
        return data


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
    compensation: dict[str, dict[str, Any]] | None = None


class PersonProfessionalsResult(BaseModel):
    prefix: str | None = None
    name: str | None = None
    biography: str | None = None
    # keyed by company_id (str) -> function name -> list of roles
    roles: dict[str, dict[str, list[PersonRole]]] = {}

    @model_validator(mode="before")
    @classmethod
    def build_name(cls, data: Any) -> Any:
        """Build name from individual name parts in the format: First Middle "Salutation" Last Suffix."""
        if isinstance(data, dict) and not data.get("name"):
            salutation = data.get("salutation")
            parts = [
                data.get("first_name"),
                data.get("middle_name"),
                f'"{salutation}"' if salutation else None,
                data.get("last_name"),
                data.get("suffix"),
            ]
            filtered = [p for p in parts if p]
            if filtered:
                data["name"] = " ".join(filtered)
        return data


class PersonProfessionalsResp(BaseModel):
    # keyed by person_id (str)
    results: dict[str, PersonProfessionalsResult]
    errors: dict[str, str] = {}
