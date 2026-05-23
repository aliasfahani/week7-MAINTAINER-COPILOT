import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Maintainer's Copilot", layout="wide")
st.title("Maintainer's Copilot")

if "token" not in st.session_state:
    st.session_state.token = ""


def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}


def response_json(response):
    try:
        return response.json()
    except ValueError:
        return None


def show_api_result(response):
    """Render API responses without assuming every error body is JSON.

    FastAPI can return plain-text "Internal Server Error" for unhandled errors.
    Streamlit's st.json tries to parse strings as JSON, which caused the widget
    admin tab to show a JSON parser error instead of the actual API problem.
    """

    payload = response_json(response)
    if response.ok:
        st.json(payload if payload is not None else {"response": response.text})
        return
    if isinstance(payload, dict):
        st.error(payload.get("detail", payload))
    else:
        st.error(response.text)


with st.sidebar:
    st.header("Login")
    email = st.text_input("Email", value="admin@example.com")
    password = st.text_input("Password", type="password", value="admin123")
    if st.button("Login"):
        response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password}, timeout=10)
        if response.ok:
            st.session_state.token = response.json()["access_token"]
            st.success("Logged in")
        else:
            st.error(response.text)

tabs = st.tabs(["Chat", "Memory", "Widget Admin"])

with tabs[0]:
    st.subheader("Chat")
    conversation_id = st.text_input("Conversation ID", value="demo-conversation")
    title = st.text_input("Issue title")
    body = st.text_area("Issue body")
    message = st.text_area("Message", value="Classify this issue and search similar resolved issues")
    if st.button("Send chat"):
        payload = {"conversation_id": conversation_id, "message": message, "issue": {"title": title, "body": body}}
        response = requests.post(f"{API_URL}/chat", json=payload, headers=headers(), timeout=30)
        if response.ok:
            data = response.json()
            st.write(data["answer"])
            with st.expander("Tool calls and raw results"):
                st.json(data["tool_calls"])
            st.caption(f"trace_id: {data['trace_id']}")
        else:
            st.error(response.text)
            st.warning("Check that the API is running on API_URL and that you are logged in.")

with tabs[1]:
    st.subheader("Memory Inspector")
    if st.button("Load memories"):
        response = requests.get(f"{API_URL}/memory", headers=headers(), timeout=10)
        show_api_result(response)
    memory_text = st.text_area("New semantic memory")
    if st.button("Write memory"):
        response = requests.post(f"{API_URL}/memory", json={"text": memory_text, "metadata": {"source": "streamlit"}}, headers=headers(), timeout=10)
        show_api_result(response)

with tabs[2]:
    st.subheader("Widget Admin")
    widget_id = st.text_input("Widget ID", value="demo-widget")
    allowed = st.text_input("Allowed origins", value="*")
    greeting = st.text_input("Greeting", value="Hi! How can I help?")
    primary = st.color_picker("Primary color", value="#2563eb")
    if st.button("Create widget"):
        payload = {
            "widget_id": widget_id,
            "allowed_origins": [item.strip() for item in allowed.split(",")],
            "theme": {"primaryColor": primary},
            "greeting": greeting,
            "enabled_tools": ["classify_issue", "rag_search", "summarize_thread"],
        }
        response = requests.post(f"{API_URL}/admin/widgets", json=payload, headers=headers(), timeout=10)
        show_api_result(response)
    st.code(f'<script src="{API_URL}/widget.js" data-widget-id="{widget_id}"></script>', language="html")
