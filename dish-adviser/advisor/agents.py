import json
import os
from typing import List, Union

from langchain.agents import initialize_agent, AgentType
from langchain.agents.conversational_chat.output_parser import ConvoOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, RedisChatMessageHistory
from langchain.output_parsers.json import parse_json_markdown
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.tools import Tool

from advisor.prompts import FUNCTION_AGENT_PROMPT_PREFIX, FUNCTION_AGENT_PROMPT_SUFFIX, \
    FUNCTION_AGENT_FORMAT_INSTRUCTIONS
from advisor.tools import MongoDbSearchTool


class ConvoOutputCustomParser(ConvoOutputParser):
    """Output parser for the conversational agent."""

    def get_format_instructions(self) -> str:
        """Returns formatting instructions for the given output parser."""
        return FUNCTION_AGENT_FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Attempts to parse the given text into an AgentAction or AgentFinish.

        Raises:
             OutputParserException if parsing fails.
        """
        try:
            # Attempt to parse the text into a structured format (assumed to be JSON
            # stored as markdown)
            try:
                response = json.loads(text)
            except Exception:
                response = parse_json_markdown(text)

            # If the response contains an 'action' and 'action_input'
            if "action" in response and "action_input" in response:
                action, action_input = response["action"], response["action_input"]

                # If the action indicates a final answer, return an AgentFinish
                if action == "Final Answer":
                    restaurant_ids = response["restaurant_ids"]
                    ids = "\n\nRestaurant Ids: " + ",".join(restaurant_ids) if len(restaurant_ids) > 0 else ""
                    return AgentFinish({"output": action_input + ids}, text)
                else:
                    # Otherwise, return an AgentAction with the specified action and
                    # input
                    return AgentAction(action, action_input, text)
            else:
                # If the necessary keys aren't present in the response, raise an
                # exception
                raise OutputParserException(
                    f"Missing 'action' or 'action_input' in LLM output: {text}"
                )
        except Exception:
            return AgentFinish({"output": text}, text)


class ConversationalAgentFactory:
    def __init__(self, tools: List[Tool], llm: ChatOpenAI):
        self.tools = tools
        self.llm = llm
        history = RedisChatMessageHistory(session_id="123", key_prefix='DISHER_ADVISER:')
        self.memory = ConversationBufferMemory(memory_key="chat_history", llm=llm, max_token_limit=1000, chat_memory=history, return_messages=True)

    def get_agent(self):
        agent_executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            agent_kwargs={
                "system_message": FUNCTION_AGENT_PROMPT_PREFIX,
                "human_message": FUNCTION_AGENT_PROMPT_SUFFIX,
                "output_parser": ConvoOutputCustomParser(), # enable this if work with gpt-3.5
            }
        )
        return agent_executor


def load_openai_key():
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        print("OPENAI_API_KEY is not set")
        exit(1)
    else:
        print("OPENAI_API_KEY is set")


def init_convo_agent():
    load_openai_key()
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    mongo_tool = MongoDbSearchTool().as_tool()
    tools = [mongo_tool]
    return ConversationalAgentFactory(llm=llm, tools=tools).get_agent()