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
