from enum import Enum
import inspect
from pathlib import Path

from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic._internal._repr import display_as_type

from kfinance.kfinance import Client
from kfinance.tool_calling import ALL_TOOLS, KfinanceTool


def add_tool_calling_docs_for_all_tools() -> None:
    """Add tool calling documentation for all tools.

    Adding tool calling documentation involves two steps:
    - Add a function definition to the tool file
    - Add the module to tool_calling.rst to instruct sphinx what tool functions to document.

    Do not commit changes that result from executing this function.
    """

    for tool_cls in ALL_TOOLS:
        tool = tool_cls(kfinance_client=Client(refresh_token="fake"))
        add_function_to_tools_file(tool)
        add_module_to_tool_calling_rst(tool)


def add_function_to_tools_file(tool: KfinanceTool) -> None:
    """Add a function definition to each tool file, which mimics the tool definition passed to LLMs

    The KfinanceTools are primarily intended to be transpiled for use with langchain, openai,
    anthropic etc. However, the automatically generated documentation is not very helpful.
    Instead, we use the tool definition to create a function definition that's close to what we
    pass to the LLM. We then use sphinx to generate docs only for these generated functions.

    We append the function definition to the same file as the tool. This ensures that the
    [source] field in the documentation links to the file where the tool is defined.

    Here's an example from the `GetNQuartersAgo` tool:

    def get_n_quarters_ago(n: int) -> kfinance.constants.YearAndQuarter:
        '''Get the year and quarter corresponding to [n] quarters before the current quarter.

        :param n: Number of quarters before the current quarter
        :type n: int
        :rtype: YearAndQuarter'''

    """

    # The signature built with the inspect module does not include necessary imports.
    imports = ["import kfinance", "import datetime", "from typing import Optional"]
    signature_str = build_signature_str(tool)

    # Use inspect to retrieve the return type and add it to the imports if it's not a builtin.
    return_annotation = inspect.signature(tool._run).return_annotation
    if return_annotation.__module__ != "builtins":
        imports.append(f"from {return_annotation.__module__} import {return_annotation.__name__}")

    # Generate sphinx style annotations for each param.
    openai_params = convert_to_openai_tool(tool)["function"]["parameters"]["properties"]
    args = ""
    for field_name, field_metadata in tool.args_schema.model_fields.items():
        # We use the openai definition to extract the field description. This means that, just like
        # pydantic/langchain, we use the docstring of an enum as the description for an enum field.
        args += f"\n    :param {field_name}: {openai_params[field_name]['description']}"
        args += f"\n    :type {field_name}: {display_as_type(field_metadata.annotation)}"

    func_str = "\n" + "\n".join(imports) + "\n"
    func_str += f"{signature_str}"
    func_str += f'\n    """{tool.description}\n'
    func_str += args
    # Add sphinx style return annotation
    func_str += f'\n    :rtype: {return_annotation.__name__}"""'

    # Write definition to tool file
    with open(inspect.getfile(tool.__class__), mode="a") as f:
        f.write(func_str)


def build_signature_str(tool: KfinanceTool) -> str:
    """Return the signature string of the tool

    Return value example:
        def get_latest(use_local_timezone: bool = True) -> kfinance.constants.LatestPeriods:

    This function is mostly necessary for proper enum handling.
    inspect.Parameter uses __repr__ to stringify enum default values, not __str__.
    As a result, it formats default values as "<Periodicity.day: 'day'>" rather than
    "Periodicity.day".
    """
    signature = inspect.signature(tool._run)

    for param in signature.parameters.values():
        if isinstance(param.default, Enum):
            # For enums, redirect __repr__ to __str__
            param.default.__class__.__repr__ = param.default.__class__.__str__
    return f"def {tool.name}{signature}:"


def add_module_to_tool_calling_rst(tool: KfinanceTool) -> None:
    """Add a module for each tool to tool_calling.rst.

    We only want to include the generated function in the docs.

    Example:
        .. automodule:: kfinance.tool_calling.get_latest
        :members: get_latest
    """

    module_str = "\n"
    module_str += f"\n.. automodule:: {tool.__module__}"
    module_str += f"\n    :members: {tool.name}"

    with open(Path(Path(__file__).resolve().parent, "tool_calling.rst"), mode="a") as f:
        f.write(module_str)

if __name__ == "__main__":
    add_tool_calling_docs_for_all_tools()