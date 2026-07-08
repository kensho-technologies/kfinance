# %%NBQA-CELL-SEP13882f
# install the latest version of kFinance package
hash(0x8B48147C)
# install the LLM Python package
hash(0x5856B13)


# %%NBQA-CELL-SEP13882f
import json

# import the kfinance client
from kfinance.client.kfinance import Client

# check if the current environment is a Google Colab
try:
    import google.colab

    IN_GOOGLE_COLAB = True
except:
    IN_GOOGLE_COLAB = False

# initialize the kfinance client with one of the following:
# 1. your kensho refresh token
# 2. your kensho client id and kensho private key
# 3. automated login (not accessible on Google Collab)
if IN_GOOGLE_COLAB:
    kensho_refresh_token = ""
    assert kensho_refresh_token != "", "kensho refresh token is empty! Make sure to enter your kensho refresh token above"
    kfinance_client = Client(refresh_token=kensho_refresh_token)

    # kensho_client_id = ""
    # kensho_private_key = ""
    # assert kensho_client_id != "", "kensho client id is empty! Make sure to enter your kensho client id above"
    # assert kensho_private_key != "", "kensho private key is empty! Make sure to enter your kensho private key above"
    # kfinance_client = Client(client_id=kensho_client_id, private_key=kensho_private_key)
else:
    kfinance_client = Client()


# %%NBQA-CELL-SEP13882f
from kfinance.integrations.tool_calling.prompts import BASE_PROMPT
from typing import Any, cast

# import Anthropic
from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock
from anthropic.types import ToolParam, Message, MessageParam, ToolResultBlockParam


def text_from_response_message(response_message: Any) -> str | None:
    if response_message.content is None:
        return None
    if isinstance(response_message.content, list):
        text_blocks = list(filter(lambda c: isinstance(c, TextBlock), response_message.content))
        if text_blocks:
            return text_blocks[0].text
        elif not isinstance(response_message.content, list):
            return response_message.content.text  # type: ignore[unreachable]
        return None
    return None


def tool_calls_from_response_message(response_message: Any) -> list:
    if not isinstance(response_message.content, list):
        return []
    return list(filter(lambda c: isinstance(c, ToolUseBlock), response_message.content))


class AnthropicChat:
    def __init__(self, kfinance_client: Client) -> None:
        # initialize Anthropic with your Anthropic API key
        anthropic_api_key = ""  # replace with your own key
        assert anthropic_api_key != "", "Anthropic API key is empty! Make sure to enter your Anthropic API key above"
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        # initialize the kFinance client
        self.kfinance_client = kfinance_client
        # initialize tools and tool descriptions
        self.tools = kfinance_client.tools
        self.tool_descriptions: list[
            ToolParam] = cast(list[ToolParam], kfinance_client.anthropic_tool_descriptions)
        self.messages: list[MessageParam] = []

    def print_response(self) -> Message:
        response = self.anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            # you can use any Anthropic model that supports tool calling
            system=BASE_PROMPT,
            messages=self.messages,
            tools=self.tool_descriptions,
            max_tokens=2048,
        )
        response_message = response
        self.messages.append({"role": "assistant", "content": response_message.content})
        response_message_text = text_from_response_message(response_message)
        if response_message_text is not None:
            print("\nAssistant Response:")
            print(response_message_text)
        return response_message

    def print_responses(self, user_input: str) -> None:
        # add user input message
        self.messages.append({"role": "user", "content": user_input})
        while True:
            response = self.anthropic.messages.create(
                model="claude-3-7-sonnet-20250219",
                system=BASE_PROMPT,
                messages=self.messages,
                tools=self.tool_descriptions,
                max_tokens=2048,
            )

            tool_calls = tool_calls_from_response_message(response)
            if tool_calls:
                self.messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for tool_call in tool_calls:
                    function_name = tool_call.name
                    args = tool_call.input
                    print(f"\nCalling `{function_name}` with:\n{json.dumps(args, indent=2)}")
                    try:
                        result = self.tools[function_name](**args)
                        print(f"Tool `{function_name}` result: {result}")
                        tool_results.append(ToolResultBlockParam(
                            type="tool_result",
                            tool_use_id=tool_call.id,
                            content=str(result)
                        ))
                    except Exception as e:
                        print(f"Tool `{function_name}` failed: {e}")
                        tool_results.append(ToolResultBlockParam(
                            type="tool_result",
                            tool_use_id=tool_call.id,
                            content=str(e),
                            is_error=True
                        ))

                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })
                continue

            # append final assistant message
            self.messages.append({
                "role": "assistant",
                "content": response.content
            })
            response_message_text = text_from_response_message(response)
            if response_message_text is not None:
                print("\nAssistant Response:")
                print(response_message_text)
            break

    def start_chatting(self) -> None:
        """Open chat shell"""
        while True:
            user_input = input("Enter your message and press the [return] key\n")
            self.print_responses(user_input)
            print()


# %%NBQA-CELL-SEP13882f
# instantiate the AnthropicChat with the kfinance client
anthropic_chat = AnthropicChat(kfinance_client)
# start chatting with the Anthropic
anthropic_chat.start_chatting()
