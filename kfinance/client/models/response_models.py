import logging
from typing import Any, Callable, Dict, Generic, TypeAlias, TypeVar

from pydantic import BaseModel, Field, model_serializer, model_validator


logger = logging.getLogger(__name__)


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


class SingleResultResp(BaseModel, Generic[T]):
    """Generic response class that unwraps a single result from the API's multi-result format.

    - `error` is always the last field in the response.
    - `error` is only included if there is an error.
    """

    result: T | None = None
    error: str | None = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: Callable) -> Dict[str, Any]:
        """Make `error` the last response field and only include if there is an error."""
        data = handler(self)
        error = data.pop("error")
        if error:
            data["error"] = error
        return data

    @model_validator(mode="before")
    @classmethod
    def from_post_response(cls, data: Any) -> Any:
        """Extract the single result from the API response."""
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            if len(results) > 1:
                logger.warning("Expected at most one result, got %d", len(results))
            result = next(iter(results.values()), None)
            errors = data.get("errors", {})
            if len(errors) > 1:
                logger.warning("Expected at most one error, got %d", len(errors))
            error = next(iter(errors.values()), None)
            return {"result": result, "error": error}
        return data
