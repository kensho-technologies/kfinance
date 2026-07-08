# %%NBQA-CELL-SEP13882f
# install the latest version of kFinance package
hash(0x5E147C05)
# install the LLM Python package
hash(0xB41CE4DE)


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
from typing import cast
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam, \
    ChatCompletionAssistantMessageParam, ChatCompletionSystemMessageParam, ChatCompletionToolParam, \
    ChatCompletionMessageFunctionToolCall
# import OpenAI
from openai import OpenAI


# the OpenAIChat class is used to create a chat loop that automatically executes tool calls
class OpenAIChat:
    def __init__(self, kfinance_client: Client) -> None:
        # initialize OpenAI with your OpenAI API key
        openai_api_key = ""  # replace with your own key
        assert openai_api_key != "", "OpenAI API key is empty! Make sure to enter your OpenAI API key above"
        # client config for OpenAI. There are other ways to access OpenAI
        self.openai = OpenAI(api_key=openai_api_key)
        # initialize the kFinance client
        self.kfinance_client = kfinance_client
        # initialize tools and tool descriptions
        self.tools = kfinance_client.tools
        self.tool_descriptions: list[ChatCompletionToolParam] = cast(list[ChatCompletionToolParam], kfinance_client.openai_tool_descriptions)
        # set the first message to include the system prompt
        self.messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=BASE_PROMPT),
        ]

    def print_response(self) -> ChatCompletionMessage:
        """Print and return response"""
        # try to send the message history to OpenAI and get the response
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # you can use any OpenAI model that supports tool calling
                messages=self.messages,
                tools=self.tool_descriptions,
            )
            response_message = response.choices[0].message
            msg_dict: ChatCompletionMessageParam = cast(ChatCompletionMessageParam, response_message.model_dump())
            self.messages.append(msg_dict)
        # if there's an error, manually create a response with the error
        except Exception as e:  # noqa:BLE001
            message = ChatCompletionAssistantMessageParam(
                role="assistant", content=f"you had an error: {str(e)}"
            )
            self.messages.append(message)
            response_message = ChatCompletionMessage.model_validate(message)
        if response_message.content is not None:
            print("\nAssistant Response:")
            print(response_message.content)

        # Print tool calls if any
        if response_message.tool_calls:
            print("\nTool Calls:")
            for tool_call in response_message.tool_calls:
                assert isinstance(tool_call, ChatCompletionMessageFunctionToolCall)
                function = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print(f"- Function: {function}")
                print(f"  Arguments: {json.dumps(arguments, indent=2)}")

        return response_message

    def print_responses(self, user_input: str) -> None:
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
                assert isinstance(tool_call, ChatCompletionMessageFunctionToolCall)
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
                    print(f"\nTool `{function}` executed successfully.")
                    print(f"Output: {output}")
                # if there's an exception thrown while executing the function,
                # append the exception as a message to the message history
                except Exception as e:
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps({"output": str(e)}),
                            "tool_call_id": tool_call.id,
                        }
                    )
                    print(f"\nError while executing tool `{function}`:")
                    print(e)
            # get a new response
            response_message = self.print_response()
        return None

    def start_chatting(self) -> None:
        """Open chat shell"""
        # prompt for user input and get the OpenAI response in a loop
        while True:
            user_input = input("Enter your message and press the [return] key\n")
            self.print_responses(user_input)
            print("\n" + "-" * 60 + "\n")


# %%NBQA-CELL-SEP13882f
# instantiate the OpenAIChat with the kfinance client
openai_chat = OpenAIChat(kfinance_client)
# start chatting with the OpenAIChat
openai_chat.start_chatting()
