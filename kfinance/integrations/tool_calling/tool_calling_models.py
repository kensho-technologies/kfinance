from typing import Annotated, Any, Literal, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from kfinance.client.kfinance import Client
from kfinance.client.permission_models import Permission


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

    def run_without_langchain(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a Kfinance tool without langchain.

        Langchain converts json input params into the pydantic args_schema, which means that
        strings get turned into enums, dates, or datetimes where necessary.
        When executing a tool without langchain, we have to handle this
        conversion ourselves.
        """
        args_model = self.args_schema.model_validate(kwargs)
        args_dict = args_model.model_dump()
        # Only pass params included in the LLM generated kwargs.
        # This means that we don't use defaults defined by the pydantic models and instead use
        # the defaults defined in the `_run` function.
        # This behavior matches the langchain handling. See
        # https://github.com/langchain-ai/langchain/blob/ca39680d2ab0d786bc035930778a5787e7bb5e01/libs/core/langchain_core/tools/base.py#L595-L597
        args_dict = {k: v for k, v in args_dict.items() if k in kwargs}
        return self._run(**args_dict)

    def run_with_grounding(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a Kfinance tool with grounding support.

        This is a wrapper around the `run_without_langchain` method that adds grounding
        support, for returning the endpoint urls along with the data as citation info for the LRA Data Agent.
        """
        with self.kfinance_client.kfinance_api_client.endpoint_tracker() as endpoint_tracker_queue:
            data = self.run_without_langchain(*args, **kwargs)

            # After completion of tool data fetching and within the endpoint_tracker context manager scope, dequeue the endpoint_tracker_queue
            endpoint_urls = []
            while not endpoint_tracker_queue.empty():
                endpoint_urls.append(endpoint_tracker_queue.get())

            return {
                "data": data,
                "endpoint_urls": endpoint_urls,
            }

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """The code to execute the tool.

        Where feasible and useful, tools should use batch processing to parallelize
        requests, usually by allowing callers to pass in multiple identifiers.
        The usual processing order for functions with multiple identifiers is:
        - Parse string identifiers into `CompanyIdentifier`
        - batch fetch the required id for the api call (company/security/trading item id) via
            fetch_<relevant>_ids_from_identifiers
        - batch fetch the required info based on the ids via process_tasks_in_thread_pool_executor
        - format results for output

        Any company_ids in the response should be prefixed with the COMPANY_ID_PREFIX ("C_").
        This allows us to circumvent overlaps between tickers (which can be purely numerical)
        and company_ids. Company_ids with prefixes can be used like normal identifiers.
        For example:
        Request: get_business_relationship_from_identifiers(identifiers=["SPGI"], business_relationship="supplier")
        Response: {"SPGI": {"current": [{"company_id": "C_883103", "company_name": "A Corp"}]...
        Request: get_prices_from_identifiers(identifiers=["C_883103"])
        """
        ...


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
