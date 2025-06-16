import os
import sys

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from kfinance.kfinance import Client
from dotenv import load_dotenv

load_dotenv()

USER_INPUT_PROMPT = "Enter your message and press the [return] key\n"


class LangChainAnthropicChat:
    def __init__(self) -> None:
        """"""
        # kfinance_client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])
        kfinance_client = Client()
        llm = ChatAnthropic(  # type: ignore
            model="claude-3-7-sonnet-20250219",
            api_key=os.environ["ANTHROPIC_API_KEY"],  # type: ignore
        )

        # Get the prompt to use - can be replaced with any prompt that includes variables "agent_scratchpad" and "input"!
        BASE_PROMPT = """You are an agent that calls one or more tools to retreive data to answer questions from financial analysts. Use the supplied tools to answer the user's questions. Always use the `get_latest` function when asked about the last or most recent quarter or time period etc. Always use the `get_latest` function when a tool requires a time parameter and the time is unspecified in the question. Do not just use `get_company_id_from_ticker`, call the tools to get the needed data to answer the question. Try to use `get_financial_line_item_from_ticker` for questions about a companies finances. If the tools do not respond with data that answers the question, then respond by saying you don't have the data available. Keep calling tools until you have the answer or the tool says the data is not available. Label large numbers with "million" or "billion" and currency symbols if appropriate."""

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
        agent = create_tool_calling_agent(
            llm=llm, tools=kfinance_client.langchain_tools, prompt=prompt
        )
        # Create an agent executor by passing in the agent and tools
        self.agent_executor = AgentExecutor(
            agent=agent, tools=kfinance_client.langchain_tools, verbose=True
        )

    def start_chatting(self) -> None:
        """Open chat shell"""
        while True:
            user_input = input(USER_INPUT_PROMPT)
            self.agent_executor.invoke({"input": user_input})
            sys.stdout.write("\n")


LangChainAnthropicChat().start_chatting()