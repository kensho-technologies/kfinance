# Tool Calling

The tools defined in this directory are intended for tool calling. 

Each tool is a subclass of [KfinanceTool](shared_models.py), which is
turn a subclass of `BaseTool` from langchain. We use langchain to convert these tools 
into LLM-specific tool descriptions.

### KfinanceTool
Each `KfinanceTool` requires the following attributes to be defined:
- name: the function name
- description: the description of the function passed to an LLM. This should not include a description 
of the arguments.
- args_schema: A pydantic model defining the input schema for the function (more on that below)
- _run: the source code for the tool.

All new tools have to be added to the `ALL_TOOLS` [list](__init__.py).


When initializing a `KfinanceTool`, it's always required to pass in an initialized Kfinance 
`Client`, which can be accessed from within the tool as `self.kfinance_client`. This allows us to 
make kfinance api calls without needing to get a kfinance client passed in with every call.

If tools are called from langchain, then langchain handles the deserialization of arguments before 
calling the tools. If tools are called without langchain, then we have to handle that
deserialization ourselves. The deserialization step is handled by 
`KfinanceTool.run_without_langchain`.

### args_schema Pydantic Model
Each `KfinanceTool` has a corresponding pydantic model that defines the call arguments for the tool.
We use langchain to convert these pydantic models into llm-specific argument schemas. 
- Each field should contain a `description` and, where feasible, a `default`.
- Use of python objects is preferred over string types. For example enums, dates, and datetimes all 
work.
- The order, type, and default of arguments in the `tool_args` has to match the order, type, and 
default of arguments in the `_run` function.
- If your tool takes an `identifier` as its first argument, subclass `ToolArgsWithIdentifier` to 
ensure that the description of the identifier remains consistent across tools.