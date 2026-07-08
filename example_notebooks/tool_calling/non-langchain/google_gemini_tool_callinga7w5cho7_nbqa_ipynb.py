# %%NBQA-CELL-SEP13882f
# install the latest version of kFinance package
hash(0xDD91A195)
# install the LLM Python package
hash(0x7ABFCB91)


# %%NBQA-CELL-SEP13882f
# import the kfinance client
from kfinance.client.kfinance import Client
import json

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
# import Google's generativeai package ('Gemini')
import google.generativeai as genai


# the GeminiChat class is used to create a chat loop that automatically executes tool calls
class GeminiChat:
    def __init__(self, kfinance_client: Client) -> None:
        # initialize Gemini with your Gemini API key
        gemini_api_key = ""  # replace with your own key
        assert gemini_api_key != "", "Gemini API key is empty! Make sure to enter your Gemini API key above"
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=BASE_PROMPT,
            tools=kfinance_client.gemini_tool_descriptions
        )
        self.gemini = model.start_chat()

    def print_responses(self, user_input: str) -> None:
        """Print responses and call tools"""
        # send a message to Gemini and get the response
        response = self.gemini.send_message(user_input)
        parts = response.candidates[0].content.parts
        text_parts = list(filter(lambda part: "text" in part, parts))
        tool_parts = list(filter(lambda part: "function_call" in part, parts))

        print("\nAssistant Response:")
        for text_part in text_parts:
            print(text_part.text)
        while tool_parts != []:
            tool_outputs = []
            for tool_part in tool_parts:
                function = tool_part.function_call.name
                arguments = {
                    key: int(value) if isinstance(value, float) else value
                    for key, value in tool_part.function_call.args.items()
                }
                print(f"- Function: {function}")
                print(f"  Arguments: {json.dumps(arguments, indent=2)}")
                try:
                    output = str(kfinance_client.tools[function](**arguments))
                    print(f"\nTool `{function}` executed successfully.")
                    print(f"Output: {output}")
                except Exception as e:
                    output = str(e)
                    print(f"\nTool `{function}` failed.")
                    print(f"Error: {output}")

                tool_outputs.append(
                    f"The output of function {function} with arguments {arguments} is: {output}")

                response = self.gemini.send_message(' '.join(tool_outputs))
                parts = response.candidates[0].content.parts
                text_parts = list(filter(lambda part: "text" in part, parts))
                tool_parts = list(filter(lambda part: "function_call" in part, parts))
                print("\nAssistant Response:")
                for text_part in text_parts:
                    print(text_part.text)
        return None

    def start_chatting(self) -> None:
        """Open chat shell"""
        while True:
            user_input = input("Enter your message and press the [return] key\n")
            self.print_responses(user_input)
            print()


# %%NBQA-CELL-SEP13882f
# instantiate the GeminiChat with the kfinance client
gemini_chat = GeminiChat(kfinance_client)
# start chatting with the GeminiChat
gemini_chat.start_chatting()
