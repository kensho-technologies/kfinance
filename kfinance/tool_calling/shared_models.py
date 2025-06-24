from typing import Annotated, Any, Literal, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from kfinance.constants import Permission
from kfinance.kfinance import Client


class KfinanceTool(BaseTool):
    """KfinanceTool is a langchain base tool with a kfinance Client.

    The kfinance_client attribute allows us to make kfinance calls without needing
    the client to get passed in as a param during invocations.
    """

    kfinance_client: Client
    args_schema: Type[BaseModel]
    required_permission: Permission | None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

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

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """The code to execute the tool"""
        ...


class ToolArgsWithIdentifier(BaseModel):
    """Tool argument with an identifier.

    All tools using an identifier should subclass this model to ensure that the description
    of identifier is always the same.
    """

    identifier: str = Field(
        description="The identifier, which can be a ticker symbol, ISIN, or CUSIP"
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
