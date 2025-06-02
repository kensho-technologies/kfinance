# create a struct similar to the OpenAI response class, for manually creating responses
from collections import namedtuple
import json
import os
import sys
from typing import Any

# import OpenAI
from openai import OpenAI

from kfinance.kfinance import Client


Message = namedtuple("Message", "role content tool_calls")

# the prompt given to all LLMs to instruct them how to use tools to call the kFinance API
SYSTEM_PROMPT = "You are an LLM trying to help financial analysts. Use the supplied tools to assist the user. Always use the `get_latest` function when asked about the last or most recent quarter or time period etc. Always use the `get_latest` function when a tool requires a time parameter and the time is unspecified in the question"
# the message shown to users to prompt them to input a message
USER_INPUT_PROMPT = "Enter your message and press the [return] key\n"


# the OpenAIChat class is used to create a chat loop that automatically executes tool calls
class OpenAIChat:
    def __init__(self) -> None:
        """"""
        kfinance_client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])
        # good client config for OpenAI. There are other ways to access OpenAI
        self.openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        # initialize the kFinance client
        self.kfinance_client = kfinance_client
        # initialize tools and tool descriptions
        self.tools = kfinance_client.tools
        self.tool_descriptions = kfinance_client.openai_tool_descriptions
        # set the first message to include the system prompt
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
        ]

    def print_response(self) -> Any:
        """Print and return response"""
        # try to send the message history to OpenAI and get the response
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # you can use any OpenAI model that supports function calling
                messages=self.messages,  # type: ignore
                tools=self.tool_descriptions,  # type: ignore
            )
            response_message = response.choices[0].message
            self.messages.append(response_message)  # type: ignore
        # if there's an error, manually create a response with the error
        except Exception as e:  # noqa:BLE001
            self.messages.append({"role": "user", "content": f"you had an error: {str(e)}"})
            response_message = Message("assistant", f"an error occured: {str(e)}", None)  #  type: ignore
        # if the response contains text (and not just tool calls), print out the text
        if response_message.content is not None:
            sys.stdout.write(response_message.content)
        return response_message

    def print_responses(self, user_input: str) -> list[str]:
        """Print responses and call tools"""
        # append the current user input as a message to the message history
        self.messages.append({"role": "user", "content": user_input})
        # get the OpenAI response to the message history
        response_message = self.print_response()
        # while the response has tool calls
        while response_message.tool_calls is not None:
            # for each tool call, execute the function and arguments specified in the tool call
            # and append the output as a message to the message history
            for tool_call in response_message.tool_calls:
                function = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                # try to execute the function and arguments specified in the tool call
                try:
                    output = self.tools[function](**arguments)
                    # append the output as a message to the message history
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps({"output": str(output)}),
                            "tool_call_id": tool_call.id,
                        }
                    )
                # if there's an exception thrown while executing the function,
                # append the exception as a message to the message history
                except Exception as e:  # noqa:BLE001
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps({"output": str(e)}),
                            "tool_call_id": tool_call.id,
                        }
                    )
            # get a new response
            response_message = self.print_response()
        return None  # type: ignore

    def start_chatting(self) -> None:
        """Open chat shell"""
        # prompt for user input and get the OpenAI response in a loop
        while True:
            user_input = input(USER_INPUT_PROMPT)
            self.print_responses(user_input)
            sys.stdout.write("\n")


openai_chat = OpenAIChat()
openai_chat.start_chatting()
