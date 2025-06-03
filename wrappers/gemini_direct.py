# import Google's generativeai package ('Gemini')
import os
import sys

import google.generativeai as genai

from kfinance.kfinance import Client


# the prompt given to all LLMs to instruct them how to use tools to call the kFinance API
SYSTEM_PROMPT = "You are an LLM trying to help financial analysts. Use the supplied tools to assist the user. Always use the `get_latest` function when asked about the last or most recent quarter or time period etc. Always use the `get_latest` function when a tool requires a time parameter and the time is unspecified in the question"
# the message shown to users to prompt them to input a message
USER_INPUT_PROMPT = "Enter your message and press the [return] key\n"


# the GeminiChat class is used to create a chat loop that automatically executes tool calls
class GeminiChat:
    def __init__(self) -> None:
        """"""
        self.kfinance_client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=self.kfinance_client.gemini_tool_descriptions,
            # tools=self.kfinance_client.gemini_tool_descriptions,
        )
        self.gemini = model.start_chat()

    def print_responses(self, user_input: str) -> None:
        """Print responses and call tools"""
        # send a message to Gemini and get the response
        response = self.gemini.send_message(user_input)
        # parse text and tool calls from the response
        parts = response.candidates[0].content.parts
        text_parts = list(filter(lambda part: "text" in part, parts))
        tool_parts = list(filter(lambda part: "function_call" in part, parts))
        # print text
        for text_part in text_parts:
            sys.stdout.write(text_part.text)
        # while the response has tool calls
        while tool_parts != []:
            tool_outputs = []
            # for each tool call, execute the function and arguments specified in the tool call
            # and append the output as a message to the message history
            for tool_part in tool_parts:
                function = tool_part.function_call.name
                arguments = {}
                # convert arguments to ints if floats, since the tool descriptions schema does not work for ints
                for key, value in tool_part.function_call.args.items():
                    arguments[key] = int(value) if isinstance(value, float) else value
                # try to execute the function and arguments specified in the tool call
                # append the output to the list of tool outputs, which will be send to the model
                try:
                    output = str(self.kfinance_client.tools[function](**arguments))
                except Exception as e:  # noqa:BLE001
                    output = str(e)
                tool_outputs.append(
                    f"The output of function {function} with arguments {arguments} is: {output}"
                )

            # send the list of tool outputs to the model and get a response
            response = self.gemini.send_message(" ".join(tool_outputs))
            # parse text and tool calls from the response
            parts = response.candidates[0].content.parts
            text_parts = list(filter(lambda part: "text" in part, parts))
            tool_parts = list(filter(lambda part: "function_call" in part, parts))
            # print text
            for text_part in text_parts:
                sys.stdout.write(text_part.text)
        return None

    def start_chatting(self) -> None:
        """Open chat shell"""
        while True:
            user_input = input(USER_INPUT_PROMPT)
            self.print_responses(user_input)
            sys.stdout.write("\n")


GeminiChat().start_chatting()
