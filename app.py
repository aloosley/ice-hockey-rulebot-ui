import json
from json import JSONDecodeError
from typing import Any

import requests
import streamlit as st


TITLE = "🏒💬 IIHF (Ice-Hockey) Rulebot"
URL = "https://ice-hockey-rulebot-d4e727a4fff5.herokuapp.com"
CHAT_ENDPOINT = "context/chat/completions"


# App title
st.set_page_config(page_title=TITLE)

# Replicate Credentials
api_key: str
with st.sidebar:
    st.title(TITLE)
    st.write('This rulebot attempts to answer your questions based on the 2023/24 IIHF rulebook.')
    if 'API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        api_key = st.secrets['API_KEY']
    else:
        api_key = st.text_input('Enter the rulebot API key:', type='password')
        if len(api_key):
            st.success('Proceed to entering your prompt message! If the API key is wrong, an error will occur.', icon='👉')

    st.subheader('Parameters (currently disabled)')
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=32, max_value=128, value=120, step=8)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I assist you in understanding the IIHF 2023/24 rulebook?"}
    ]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating LLaMA2 response. Refactored from https://github.com/a16z-infra/llama2-chatbot
def generate_response_text_data(prompt_input: str) -> list[dict[str, Any]]:
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

    response = requests.post(
        url=f"{URL}/{CHAT_ENDPOINT}",
        headers=dict(access_token=api_key),
        json=dict(
            model="",
            messages=[
                dict(
                    role="user",
                    content=prompt_input,
                )
            ],
            stream=True,
            user="string",
        ),
    )

    streamed_response_content_texts: list[str] = (
        response.content
                .decode()
                .strip("data: ")
                .rstrip("\r\n\r\n")
                .split("\r\n\r\ndata: ")
    )

    response_text_data: list[dict[str, Any]] = []
    for content_text in streamed_response_content_texts:
        try:
            response_text_data.append(json.loads(content_text))
        except JSONDecodeError:
            try:
                response_text_data.append(json.loads(content_text[:content_text.find("\r\n\r\n")]))
            except JSONDecodeError:
                continue

    return response_text_data

# User-provided prompt
if prompt := st.chat_input(disabled=not api_key):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response_text_data(prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                try:
                    full_response += item["choices"][0]["delta"]["content"]
                except KeyError:
                    continue
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
