import asyncio
from typing import Annotated, Any, Callable, Dict, Literal, Type

from asyncer import syncify
from langchain_core.tools import BaseTool
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_serializer,
)

from kfinance.client.kfinance import Client
from kfinance.client.permission_models import Permission
from kfinance.httpx_utils import KfinanceHttpxClient


class KfinanceTool(BaseTool):
    """KfinanceTool is a langchain base tool with a kfinance Client.

    The kfinance_client attribute allows us to make kfinance calls without needing
    the client to get passed in as a param during invocations.
    """

    kfinance_client: Client
    args_schema: Type[BaseModel]
    accepted_permissions: set[Permission] | None = Field(
        description="The set of accepted permissions needed to access the tool. Only one of the permissions is required (or None)."
    )

    model_config = ConfigDict(extra="forbid")

    def run_without_langchain(self, *args: Any, **kwargs: Any) -> dict:
        """Execute a Kfinance tool without langchain (sync version).

        Langchain converts json input params into the pydantic args_schema, which means that
        strings get turned into enums, dates, or datetimes where necessary.
        When executing a tool without langchain, we have to handle this
        conversion ourselves.

        Note: FastMCP uses arun_without_langchain (async version) to avoid event loop conflicts.
        """
        args_model = self.args_schema.model_validate(kwargs)
        args_dict = args_model.model_dump()
        # Only pass params included in the LLM generated kwargs.
        # This means that we don't use defaults defined by the pydantic models and instead use
        # the defaults defined in the `_run` function.
        # This behavior matches the langchain handling. See
        # https://github.com/langchain-ai/langchain/blob/ca39680d2ab0d786bc035930778a5787e7bb5e01/libs/core/langchain_core/tools/base.py#L595-L597
        args_dict = {k: v for k, v in args_dict.items() if k in kwargs}
        result_model = self._run(**args_dict)
        return result_model.model_dump(mode="json", exclude_none=True)

    async def arun_without_langchain(self, *args: Any, **kwargs: Any) -> dict:
        """Execute a Kfinance tool without langchain (async version).

        This is the async equivalent of run_without_langchain, designed for use
        with async frameworks like FastMCP.
        """
        args_model = self.args_schema.model_validate(kwargs)
        args_dict = args_model.model_dump()
        # Only pass params included in the LLM generated kwargs.
        args_dict = {k: v for k, v in args_dict.items() if k in kwargs}
        result_model = await self._arun(**args_dict)
        return result_model.model_dump(mode="json", exclude_none=True)

    def run_with_grounding(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a Kfinance tool with grounding support.

        This is a wrapper around the `run_without_langchain` method that adds grounding
        support, for returning the endpoint urls along with the data as citation info for the LRA Data Agent.
        """
        with self.kfinance_client.kfinance_api_client.endpoint_tracker() as endpoint_tracker_queue:
            args_model = self.args_schema.model_validate(kwargs)
            args_dict = args_model.model_dump()
            args_dict = {k: v for k, v in args_dict.items() if k in kwargs}
            result_model = self._run(**args_dict)

            # After completion of tool data fetching and within the endpoint_tracker context manager scope, dequeue the endpoint_tracker_queue
            endpoint_urls = []
            while not endpoint_tracker_queue.empty():
                endpoint_urls.append(endpoint_tracker_queue.get())

            return {
                "data": result_model,
                "endpoint_urls": endpoint_urls,
            }

    def _run(self, *args: Any, **kwargs: Any) -> BaseModel:
        """Run a tool sync with syncify

        `syncify` closes the current event loop after the call. That loop was tied
        to the httpx client. So once the loop gets closed, the httpx can't be
        used anymore and has to be recreated.
        """

        # If the client has a non-closed event loop, use it and the associated
        # httpx client.
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                return syncify(self._arun, raise_sync_error=False)(*args, **kwargs)
        except RuntimeError:
            pass

        # If not, create a new httpx client and then execute the tool.
        self.kfinance_client.httpx_client = KfinanceHttpxClient(
            api_client=self.kfinance_client.kfinance_api_client
        )
        return syncify(self._arun, raise_sync_error=False)(*args, **kwargs)

    def _arun(self, *args: Any, **kwargs: Any) -> BaseModel:
        """Run tool asynchronously"""


class ToolArgsWithIdentifier(BaseModel):
    """Tool argument with an identifier.

    All tools using identifiers should subclass this model to ensure that the description
    of identifiers is always the same.
    """

    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, CUSIP, or company_id"
    )


class ToolArgsWithIdentifiers(BaseModel):
    """Tool argument with a list of identifiers.

    All tools using identifiers should subclass this model to ensure that the description
    of identifiers is always the same.
    """

    identifiers: list[str] = Field(
        description="The identifiers, which can be a list of ticker symbols, ISINs, or CUSIPs, or company_ids"
    )


def convert_str_to_int(v: Any) -> Any:
    """Convert strings to integers if possible."""
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return v


# Valid Quarter is a literal type, which converts strings to int before
# validating them.
# Claude seems to often pass strings to int literals, which raise a
# ValidationError during deserialization unless they have been converted
# to int.
ValidQuarter = Annotated[Literal[1, 2, 3, 4], BeforeValidator(convert_str_to_int)]


class ToolRespWithErrors(BaseModel):
    """A tool response with an `errors` field.

    - `errors` is always the last field in the response.
    - `errors` is only included if there is at least one error.
    """

    errors: list[str] = Field(default_factory=list)

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: Callable) -> Dict[str, Any]:
        """Make `errors` the last response field and only include if there is at least one error."""
        data = handler(self)
        errors = data.pop("errors")
        if errors:
            data["errors"] = errors
        return data
