from pydantic import BaseModel


class TranscriptComponent(BaseModel):
    """A transcript component with person name, text, and component type."""

    person_name: str
    text: str
    component_type: str


class RelationshipResponseNoName(BaseModel):
    """A response from the relationship endpoint before adding the company name.

    Each element in `current` and `previous` is a company_id.
    """

    current: list[int]
    previous: list[int]


class CompanyIdAndName(BaseModel):
    """A company_id and name"""

    company_id: int
    company_name: str


class RelationshipResponse(BaseModel):
    """A response from the relationship endpoint that includes both company_id and name."""

    current: list[CompanyIdAndName]
    previous: list[CompanyIdAndName]


class CompanyDescriptions(BaseModel):
    """A company summary and description"""

    summary: str
    description: str


class NativeName(BaseModel):
    """A company's native name's name and language"""

    name: str
    language: str


class CompanyOtherNames(BaseModel):
    """A company's alternate, historical, and native names"""

    alternate_names: list[str]
    historical_names: list[str]
    native_names: list[NativeName]
