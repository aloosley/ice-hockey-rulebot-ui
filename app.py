from typing import Any

import requests
import streamlit as st
from requests import Response

VERSION = "0.9.0"
TITLE = "🏒💬 IIHF (Ice-Hockey) Rulebot"
API_URL = "https://ice-hockey-rulebot-d4e727a4fff5.herokuapp.com"
# API_URL = "http://localhost:8000"
API_ENDPOINT = "context/chat/completions"
INITIAL_MESSAGE = f"I am ready to assist you in understanding the IIHF 2023/24 rule- and situation books!"


# App title
st.set_page_config(page_title=TITLE)


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": INITIAL_MESSAGE}]


# Replicate Credentials
api_key: str
with st.sidebar:
    st.title(TITLE)
    st.write(
        "This Rulebot attempts to answer your questions based on the 2023/24 IIHF rule- and situation books "
        "(here's a [demo](https://www.loom.com/share/5e5bd5ca9fc94a1ebad15825e3e81cad?sid=0975fa10-e387-4457-9376-9ddf08a0d909))."
    )
    if 'API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        api_key = st.secrets['API_KEY']
    else:
        api_key = st.text_input(
            'Enter the Rulebot API key:',
            type='password',
            help="🔑 An API key is required to try the Ice Hockey Rule Bot 🔑"
        )
        if len(api_key):
            st.success('Proceed to entering your query message! If the API key is wrong, an error will occur.', icon='👉')

    st.button('Clear Chat History', on_click=clear_chat_history)
    st.markdown(
        f"""
        This app is currently meant for demonstrative purposes only. Please limit your usage 
        (each query costs money). 
        
        For questions and requests, please contact us:
        * [Dr. Alex Loosley](https://www.linkedin.com/in/alex-loosley/)
        * [Lina Palomo](https://www.linkedin.com/in/lina-palomo/)
        * [Stefan Schusser](https://www.linkedin.com/in/stefan-schusser/)
        
        v{VERSION}
        """
    )

    show_retrieved_rules: bool = st.checkbox(
        label="Show retrieved rules", value=False,
        help=(
            "Response will show rules that semantic search found potentially relevant (-QA tags indicate "
            "[Situation Book](https://blob.iihf.com/iihf-media/iihfmvc/media/downloads/officiating%20files/situation%20handbook/230705_iihf_sitiuation_hb_2023_24_v4_5.pdf) "
            "entries)"
        )
    )
    llm_model = st.selectbox(
        label="Choose an LLM",
        options=(
            "gpt-4o-2024-08-06",
            "gpt-4o-mini-2024-07-18",
            # "o1-preview-2024-09-12",  # Not available yet in my tier
            # "o1-mini-2024-09-12",  # Not available yet in my tier
            "gpt-4-turbo-2024-04-09",
        ),
        index=0,
        help="Choose an LLM (mini models are quicker and cheaper to use, but their results may not be as reliable)"
    )
    top_k_rules = st.select_slider(
        label="Number of rules matches to interpret",
        options=(4,5,6),
        value=5,
        help=(
            "Lowering the number of rule matches means less matches for the LLM to read through (cheaper) - "
            "unless the question is highly complex, usually 4 or 5 rule matches from our rule retrieval system "
            "provides enough context for a good answer."
        )
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


# Function for pull LLM response. Refactored from https://github.com/a16z-infra/llama2-chatbot
def pull_response(query: str) -> Response:
    """Reponse data is a chat completion containing a role and content."""
    return requests.post(
        url=f"{API_URL}/{API_ENDPOINT}",
        headers=dict(access_token=api_key),
        params=dict(
            query=query,
            llm_model=llm_model,
            top_k_rules=top_k_rules,
        ),
    )


def format_rule_records(records: list[dict[str, Any]]) -> str:
    output = ""
    for key, record in records.items():
        output += (
            f"* **Rule {key}. {record['''('title', '')''']}** (score={record['''('score', 'sum')''']:.2f}, "
            f"subsections=[{', '.join(record['''('chunk_id', 'unique')'''])}]) \n"
        )
    return output.strip()


def _parse_retrieved_rules(chat_completion_response: Response) -> str:
    return format_rule_records(chat_completion_response.json()["rule_matches_df"])


def parse_response(chat_completion_response: Response, show_retrieved_rules: bool) -> str:
    relevant_rules = ""
    if show_retrieved_rules:
        relevant_rules = "*Rules Retrieved for Analysis:*\n" + _parse_retrieved_rules(chat_completion_response) + "\n---\n"

    return (
        relevant_rules +
        "*Bot Response:* \n\n" +
        chat_completion_response.json()["content"]
    )


# User-provided query
if query := st.chat_input(placeholder="Can the goalie throw the puck?", disabled=not api_key):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)


# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with ((st.chat_message("assistant"))):
        with st.spinner("Thinking..."):
            chat_completion_response: Response = pull_response(query)
            placeholder = st.empty()

            full_response: str
            if chat_completion_response.status_code == 200:
                full_response = parse_response(chat_completion_response, show_retrieved_rules)
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
