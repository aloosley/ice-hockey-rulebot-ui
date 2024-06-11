import json
from json import JSONDecodeError
from typing import Any, Optional

import requests
import streamlit as st
from requests import Response, HTTPError


VERSION = "0.5.0"
TITLE = "🏒💬 IIHF (Ice-Hockey) Rulebot"
URL = "https://ice-hockey-rulebot-d4e727a4fff5.herokuapp.com"
# URL = "http://localhost:8000"
CHAT_ENDPOINT = "context/chat/completions"
INITIAL_MESSAGE = f"How can I assist you in understanding the IIHF 2023/24 rulebook?"


# App title
st.set_page_config(page_title=TITLE)


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": INITIAL_MESSAGE}]


# Replicate Credentials
api_key: str
with st.sidebar:
    st.title(TITLE)
    st.write("This Rulebot attempts to answer your questions based on the 2023/24 IIHF rulebook (here's an [example](app/static/english-german-example.png)).")
    if 'API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        api_key = st.secrets['API_KEY']
    else:
        api_key = st.text_input('Enter the Rulebot API key:', type='password')
        if len(api_key):
            st.success('Proceed to entering your query message! If the API key is wrong, an error will occur.', icon='👉')

    st.button('Clear Chat History', on_click=clear_chat_history)
    st.markdown(
        f"""
        This app is currently meant for demonstrative purposes only. Please limit your usage 
        (each query costs money). 
        
        If you have questions or want to see a faster more accurate rulebot, please contact us:
        * [Dr. Alex Loosley](https://www.linkedin.com/in/alex-loosley/)
        * [Lina Palomo](https://www.linkedin.com/in/lina-palomo/)
        
        v{VERSION}
        """
    )

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": INITIAL_MESSAGE}
    ]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# Function for generating LLaMA2 response. Refactored from https://github.com/a16z-infra/llama2-chatbot
def pull_response(query: str) -> Response:
    """Reponse data is a chat completion containing a role and content."""
    return requests.post(
        url=f"{URL}/{CHAT_ENDPOINT}",
        headers=dict(access_token=api_key),
        params=dict(
            query=query,
        ),
    )


# User-provided query
if query := st.chat_input(disabled=not api_key):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)


# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with (st.chat_message("assistant")):
        with st.spinner("Thinking..."):
            chat_completion_response: Response = pull_response(query)
            placeholder = st.empty()

            if chat_completion_response.status_code == 200:
                full_response = chat_completion_response.json()["content"]
            elif chat_completion_response.status_code == 404:
                full_response = (
                    "It looks like the Chat Server is currently offline. Try again later or contact Alex Loosley."
                )
            elif chat_completion_response.status_code == 403:
                full_response = "Incorrect Rulebot API Key, correct it (left side bar) and try again."
            else:
                full_response = (
                    "Sorry, something went wrong. Please reach out if this error persists."
                )
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
