import time

from dotenv import load_dotenv, find_dotenv
from langchain_community.callbacks import get_openai_callback
from langchain.schema import HumanMessage, AIMessage
from openai import OpenAI

import streamlit as st
from streamlit_chat import message


def init():
    load_dotenv(find_dotenv())

    st.set_page_config(
        page_title="Your PDF Summarizer",
        page_icon=":books:",
    )
    st.header("Your PDF Summarizer :books:")

    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "client" not in st.session_state:
        st.session_state.client = OpenAI()
    if "thread" not in st.session_state:
        st.session_state.thread = None
    if "assistant" not in st.session_state:
        st.session_state.assistant = None


def get_response_from_ai(human_input):
    print("User input:", human_input)
    print("Assistant:", st.session_state.assistant)

    if "assistant" not in st.session_state or st.session_state.assistant is None:
        print('existing')
        return "Upload at least one PDF"

    print("=" * 20)
    with get_openai_callback() as cb:
        client = st.session_state.client
        thread = st.session_state.thread

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=human_input
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=st.session_state.assistant.id,
            instructions="Summarize documents and answer questions about their content."
        )
        while True:
            # Wait for 3 second
            time.sleep(1)

            # Retrieve the run status
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                messages = client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                msg = messages.data[0]
                content = msg.content[0].text.value
                print("AI response:", content)
                print("Cost:", cb)
                return content
            elif run_status.status in ['failed', 'cancelled']:
                print("Failed to run assistant")
                return "Sorry, something went wrong."
            else:
                print(f"Running status: {run_status.status}")


def main():
    load_dotenv(find_dotenv())
    init()

    user_input = st.text_input("Ask me a question about your documents")
    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        with st.spinner("Thinking..."):
            response = get_response_from_ai(user_input)
            st.session_state.messages.append(AIMessage(content=response))

    with st.sidebar:
        st.subheader("Your docs")
        uploaded_files = st.file_uploader("Upload your docs and click on 'Process'", accept_multiple_files=True,
                                          type=["pdf"])
        if st.button("Process"):
            with st.spinner("Processing"):
                client = st.session_state.client

                # Pull all files from OpenAI account. I hope the list if not too long, otherwise don't do this
                existing_files = client.files.list().data
                existing_file_names = {}
                for existing_file in existing_files:
                    existing_file_names[existing_file.filename] = existing_file.id

                file_ids = []
                for file in uploaded_files:
                    if file.name in existing_file_names:
                        print(f"File {file.name} already exists")
                        file_ids.append(existing_file_names[file.name])
                        continue
                    tool_doc = client.files.create(
                        file=file,
                        purpose='assistants'
                    )
                    file_ids.append(tool_doc.id)
                st.session_state.file_ids = file_ids

                if st.session_state.assistant:
                    st.session_state.assistant = client.beta.assistants.update(
                        st.session_state.assistant.id,
                        instructions="You are a chatbot designed to summarize PDF documents and answering "
                                     "questions about their content.",
                        model="gpt-4-1106-preview",
                        tools=[{'type': 'retrieval'}],
                        file_ids=file_ids
                    )
                else:
                    st.session_state.assistant = client.beta.assistants.create(
                        instructions="You are a chatbot designed to summarize PDF documents and answering "
                                     "questions about their content.",
                        model="gpt-4-1106-preview",
                        tools=[{"type": "retrieval"}],
                        file_ids=file_ids
                    )
                if "thread" in st.session_state:
                    st.session_state.thread = client.beta.threads.create()

    messages = st.session_state.get('messages', [])
    for i, msg in enumerate(messages):
        if msg.type == "human":
            message(msg.content, is_user=True, avatar_style="thumbs", key=str(i) + "_user")
        elif msg.type == "ai":
            message(msg.content, is_user=False, avatar_style="avataaars", key=str(i) + "_ai")


if __name__ == "__main__":
    main()
