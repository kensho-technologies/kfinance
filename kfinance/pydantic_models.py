from pydantic import BaseModel


class TranscriptComponent(BaseModel):
    """A transcript component with person name, text, and component type."""

    person_name: str
    text: str
    component_type: str
