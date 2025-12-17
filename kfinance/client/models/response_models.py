from typing import Any, Callable, Dict, Generic, TypeAlias, TypeVar

from pydantic import BaseModel, Field, model_serializer


T = TypeVar("T", bound=BaseModel)

Source: TypeAlias = dict[str, str]


class RespWithErrors(BaseModel):
    """A response with an `errors` field.

    - `errors` is always the last field in the response.
    - `errors` is only included if there is at least one error.
    """

    errors: dict[str, str] = Field(default_factory=dict)

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: Callable) -> Dict[str, Any]:
        """Make `errors` the last response field and only include if there is at least one error."""
        data = handler(self)
        errors = data.pop("errors")
        if errors:
            data["errors"] = errors
        return data


class PostResponse(RespWithErrors, Generic[T]):
    """Generic response class that wraps results and errors from API calls."""

    results: dict[str, T]
