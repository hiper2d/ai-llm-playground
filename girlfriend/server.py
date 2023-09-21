import os

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.callbacks import get_openai_callback
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import (
    AIMessage,
    HumanMessage
)
from playsound import playsound
from streamlit_chat import message

from prompts import PROMPT, SIMPLE_PROMPT


def create_chain():
    # template = SIMPLE_PROMPT  # 0.001 per message
    template = PROMPT  # 0.024 per message

    prompt = PromptTemplate(
        input_variables=["history", "human_input"],
        template=template
    )

    return LLMChain(
        llm=OpenAI(temperature=0.2),
        prompt=prompt,
        verbose=True,
        memory=ConversationBufferWindowMemory(ai_prefix="Simona", k=20)
    )


def get_response_from_ai(human_input):
    with get_openai_callback() as cb:
        if 'chain' not in st.session_state:
            st.session_state.chain = create_chain()

        output = st.session_state.chain.predict(human_input=human_input)
        print(cb)
        return output


def init():
    load_dotenv(find_dotenv())
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        print("OPENAI_API_KEY is not set")
        exit(1)
    else:
        print("OPENAI_API_KEY is set")

    st.set_page_config(
        page_title="EE Girlfriend",
        page_icon="👩",
    )
    st.header("Electrical Engineering Girlfriend 👩")

    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def get_voice_message(message):
    payload = {
        "text": message,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0,
        }
    }

    headers = {
        "accept": "audio/mpeg",
        "xi-api-key": os.getenv("ELEVEN_LABS_API_KEY"),
        "Content-Type": "application/json"
    }

    response = requests.post('https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM?optimize_streaming_latency=0', json=payload, headers=headers)
    print(response.status_code)
    if response.status_code == 200 and response.content:
        with open("audio.mp3", "wb") as f:
            f.write(response.content)
        playsound("audio.mp3")
        return response.content


def main():
    init()

    with st.sidebar:
        user_input = st.text_input("your message", value="")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.spinner("Thinking..."):
            response = get_response_from_ai(user_input)
            get_voice_message(response)
            st.session_state.messages.append(AIMessage(content=response))

    messages = st.session_state.get('messages', [])
    for i, msg in enumerate(messages):
        if i % 2 == 0:
            message(msg.content, is_user=True, avatar_style="pixel-art-neutral", key=str(i) + "_user")
        else:
            # avatar_style="bottts-neutral" is what in README.md screenshot
            message(msg.content, is_user=False, avatar_style="avataaars", key=str(i) + "_ai")


if __name__ == '__main__':
    main()
