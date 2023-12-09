from dotenv import load_dotenv, find_dotenv

import streamlit as st
from streamlit_chat import message


def init():
    load_dotenv(find_dotenv())

    st.set_page_config(
        page_title="🕸️ Web Scraper",
        page_icon="🕸️",
    )
    st.header("🕸 Web Scraper")

    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def main():
    init()

    with st.sidebar:
        user_input = st.text_input("your message", value="")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if user_input:
        st.session_state.messages.append({"content": user_input, "is_user": True})
        with st.spinner("Thinking..."):
            response = "hi"
            st.session_state.messages.append({"content": response, "is_user": False})

    messages = st.session_state.get('messages', [])
    for i, msg in enumerate(messages):
        if i % 2 == 0:
            message(msg.content, is_user=True, avatar_style="thumbs", key=str(i) + "_user")
        else:
            message(msg.content, is_user=False, avatar_style="avataaars", key=str(i) + "_ai")


if __name__ == "__main__":
    main()