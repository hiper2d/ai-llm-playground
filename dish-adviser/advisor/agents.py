import json
import os
import re
from typing import List, Union

import redis

from advisor.tools import MongoDbSearchTool
from langchain.agents import initialize_agent, AgentType
from langchain.agents.conversational_chat.output_parser import ConvoOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, RedisChatMessageHistory
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.tools import Tool
from advisor.prompts import FUNCTION_AGENT_FORMAT_INSTRUCTIONS, FUNCTION_AGENT_PROMPT_PREFIX, FUNCTION_AGENT_PROMPT_SUFFIX


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
            # This is a hacky hack. For some reason the default ConvoOutputParser fails to parse a markdown Json
            # I had to implement my own parse_json_markdown method
            replaced_text = text.replace('\n', '').replace('\\n', '').replace('\\', '')
            match = re.search(r"```(json)?(.*)```", replaced_text, re.DOTALL)

            if match is None:
                json_str = replaced_text
            else:
                json_str = match.group(2)
            json_str = json_str.strip()
            response = json.loads(json_str)

            # If the response contains an 'action' and 'action_input'
            if "action" in response and "action_input" in response:
                action, action_input = response["action"], response["action_input"]

                # If the action indicates a final answer, return an AgentFinish
                if action == "Final Answer":
                    restaurant_ids = response["restaurant_ids"]
                    ids = "##: " + ",".join(restaurant_ids) if len(restaurant_ids) > 0 else ""
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
            print("Could not parse LLM Markdown/JSON output: " + text)
            return AgentFinish({"output": text}, text)


class ConversationalAgentFactory:
    def __init__(self, tools: List[Tool], llm: ChatOpenAI, session_id: str):
        self.tools = tools
        self.llm = llm

        redis_url = os.getenv("REDIS_GMATE_URL")
        history = RedisChatMessageHistory(
            session_id=session_id,
            url=redis_url,
            key_prefix='DISHER_ADVISER:'
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            llm=llm, max_token_limit=1000,
            chat_memory=history,
            return_messages=True
        )

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
                "output_parser": ConvoOutputCustomParser(),
            }
        )
        return agent_executor


def load_openai_key():
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        print("OPENAI_API_KEY is not set")
        exit(1)
    else:
        print("OPENAI_API_KEY is set")


def init_convo_agent(session_id):
    load_openai_key()
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    mongo_tool = MongoDbSearchTool().as_langchain_tool()
    tools = [mongo_tool]
    return ConversationalAgentFactory(llm=llm, tools=tools, session_id=session_id).get_agent()
