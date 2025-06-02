import os
import sys
from typing import Any

# import Anthropic and necessary Antrhopic types
from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock

from kfinance.kfinance import Client


# the prompt given to all LLMs to instruct them how to use tools to call the kFinance API
SYSTEM_PROMPT = "You are an LLM trying to help financial analysts. Use the supplied tools to assist the user. Always use the `get_latest` function when asked about the last or most recent quarter or time period etc. Always use the `get_latest` function when a tool requires a time parameter and the time is unspecified in the question"
# the message shown to users to prompt them to input a message
USER_INPUT_PROMPT = "Enter your message and press the [return] key\n"


# parse response message for text
def text_from_response_message(response_message: Any) -> Any:
    """"""
    if response_message.content is None:
        return None
    if (
        isinstance(response_message.content, list)
        and list(filter(lambda c: isinstance(c, TextBlock), response_message.content)) != []
    ):
        return list(filter(lambda c: isinstance(c, TextBlock), response_message.content))[0].text
    elif not isinstance(response_message.content, list):
        return response_message.content.text
    return None


# parts response message for tool calls
def tool_calls_from_response_message(response_message: Any) -> list:
    """"""
    if not isinstance(response_message.content, list):
        return []
    return list(
        filter(
            lambda c: isinstance(
                c,
                ToolUseBlock,
            ),
            response_message.content,
        )
    )


# the AntropicChat class is used to create a chat loop that automatically executes function calls
class AnthropicChat:
    def __init__(self) -> None:
        """"""
        kfinance_client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])
        self.anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        # initialize the kFinance client
        self.kfinance_client = kfinance_client
        # initialize tools and tool descriptions
        self.tools = kfinance_client.tools
        self.tool_descriptions = kfinance_client.anthropic_tool_descriptions
        # initialize the message history
        self.messages: Any = []

    def print_response(self) -> Any:
        """Print and return response"""
        # try to send the message history to Anthropic and get the response
        response = self.anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            # you can use any Anthropic model that supports function calling
            system=SYSTEM_PROMPT,
            messages=self.messages,
            tools=self.tool_descriptions,  # type: ignore
            max_tokens=2048,
        )
        response_message = response
        self.messages.append({"role": "assistant", "content": response_message.content})
        # if the response contains text , print out the text
        response_message_text = text_from_response_message(response_message)
        if response_message_text is not None:
            sys.stdout.write(response_message_text)

        return response_message

    def print_responses(self, user_input: str) -> list[str]:
        """Print responses and call tools"""
        # append the current user input as a message to the message history
        self.messages.append({"role": "user", "content": user_input})
        # get the Anthropic response to the message history
        response_message = self.print_response()
        # while the response has tool calls
        tool_calls = tool_calls_from_response_message(response_message)
        while tool_calls != []:
            # for each tool call, execute the function and arguments specified in the tool call
            # and append the output as a message to the message history
            for tool_call in tool_calls:
                function = tool_call.name
                arguments = tool_call.input
                # try to execute the function and arguments specified in the tool call
                try:
                    output = self.tools[function](**arguments)
                    # append the output as a message to the message history
                    self.messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "content": str(output),
                                    "tool_use_id": tool_call.id,
                                }
                            ],
                        }
                    )
                # if there's an exception thrown while executing the function,
                # append the exception as a message to the message history
                except Exception as e:  # noqa:BLE001
                    self.messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "content": str(e),
                                    "tool_use_id": tool_call.id,
                                    "is_error": True,
                                }
                            ],
                        }
                    )
            # get a new response and parse tool calls
            response_message = self.print_response()
            tool_calls = tool_calls_from_response_message(response_message)
        return None  # type: ignore

    def start_chatting(self) -> None:
        """Open chat shell"""
        # prompt for user input and get the Anthropic response in a loop
        while True:
            user_input = input(USER_INPUT_PROMPT)
            self.print_responses(user_input)
            sys.stdout.write("\n")


AnthropicChat().start_chatting()
