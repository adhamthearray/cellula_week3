import streamlit as st
import requests

st.set_page_config(page_title="AI Code Assistant", page_icon="🤖", layout="wide")

API_BASE = "http://127.0.0.1:" + str(__import__("os").getenv("API_PORT", "8001"))

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("AI Code Assistant")
st.caption("Explain code, generate code with RAG, and execute it safely")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("intent"):
            st.caption(f"Intent: {message['intent']}")
        if message.get("execution"):
            st.code(message["execution"])

prompt = st.chat_input("Ask about code or request a solution")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        response = requests.post(f"{API_BASE}/chat", json={"message": prompt}, timeout=60)
        payload = response.json()

    assistant_text = payload.get("answer", "")
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_text,
        "intent": payload.get("intent"),
        "execution": payload.get("execution_result"),
    })
    with st.chat_message("assistant"):
        st.markdown(assistant_text)
        st.caption(f"Intent: {payload.get('intent', '')}")
        if payload.get("execution_result"):
            st.code(payload.get("execution_result"))
