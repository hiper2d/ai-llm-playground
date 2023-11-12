from typing import Optional

import langchain
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from langchain.callbacks import get_openai_callback
from langchain.schema import HumanMessage, AIMessage
from streamlit_chat import message

from agent.assistant import Assistant, AssistantResponse
from agent.voicer import Voicer

langchain.debug = True


def init():
    load_dotenv(find_dotenv())

    st.set_page_config(
        page_title="Your Restaurant Advisor",
        page_icon="👩‍🍳",
    )
    st.header("Your Restaurant Advisor 👩‍🍳")

    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def setup_agent():
    if 'agent' not in st.session_state:
        st.session_state.agent = Assistant()
        st.session_state.voicer = Voicer()


def get_response_from_ai(human_input):
    setup_agent()
    print("="*20)
    with get_openai_callback() as cb:
        result: Optional[AssistantResponse] = st.session_state.agent.run(human_input)
        print("Cost:", cb)
        return result.reply if result else "Sorry, something went wrong."


def main():
    init()

    with st.sidebar:
        user_input = st.text_input("your message", value="")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    response = None
    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.spinner("Thinking..."):
            response = get_response_from_ai(user_input)
            st.session_state.messages.append(AIMessage(content=response))

    messages = st.session_state.get('messages', [])
    for i, msg in enumerate(messages):
        if i % 2 == 0:
            message(msg.content, is_user=True, avatar_style="thumbs", key=str(i) + "_user")
        else:
            message(msg.content, is_user=False, avatar_style="avataaars", key=str(i) + "_ai")

    # Voice generation is disabled for now because I haven't figured out if it is needed yet
    # if response and len(response) < 300:
    #    st.session_state.voicer.text_to_speech(response)


if __name__ == "__main__":
    main()
