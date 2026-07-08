# %%NBQA-CELL-SEP13882f
# install the latest version of kFinance package
hash(0xEF0875C7)
# install langchain and openai
hash(0x1B508611)
hash(0x5D62A36)
hash(0xD1E2E41)


# %%NBQA-CELL-SEP13882f
# import the kfinance client
import sys
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
from pydantic import SecretStr
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


class LangChainOpenAIChat:
    def __init__(self, kfinance_client: Client) -> None:
        # Initialize OpenAI with your OpenAI API key
        openai_api_key = SecretStr("") # replace with your own key
        assert openai_api_key != "", "OpenAI API key is empty! Make sure to enter your OpenAI API key above"
        llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
   
        # Prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", BASE_PROMPT),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        # Construct the tool calling agent
        agent = create_tool_calling_agent(llm=llm, tools=kfinance_client.langchain_tools, prompt=prompt)
        # Create an agent executor by passing in the agent and tools
        self.agent_executor = AgentExecutor(agent=agent, tools=kfinance_client.langchain_tools, verbose=True)

    def start_chatting(self) -> None:
        """Open chat shell"""
        while True:
            user_input = input("Enter your message and press the [return] key\n")
            self.agent_executor.invoke({"input": user_input})
            sys.stdout.write("\n")


# %%NBQA-CELL-SEP13882f
# instantiate LangChainOpenAIChat with the kfinance client
openai_chat = LangChainOpenAIChat(kfinance_client)
# start chatting with LangChainOpenAIChat
openai_chat.start_chatting()
