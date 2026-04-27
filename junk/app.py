import uuid

import streamlit as st

from backend.agent.agent import agent


st.set_page_config(page_title="Local Bussiness AI Agent", layout="centered")
st.title("Local Bussiness AI Agent")
st.caption("Ask for food, PG, or shops in your area")


if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"local-business-{uuid.uuid4()}"

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.thread_id = f"local-business-{uuid.uuid4()}"
    st.rerun()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


user_input = st.chat_input("")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages = st.session_state.messages[-8:]
    with st.chat_message("user"):
        st.write(user_input)

    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
        with st.spinner("Thinking.."):
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config,
                )
                raw_content = result["messages"][-1].content if isinstance(result, dict) else result
                bot_response = raw_content if isinstance(raw_content, str) else str(raw_content)
            except Exception as exc:
                bot_response = f"Error: {exc}"

        st.write(bot_response)

    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    st.rerun()
