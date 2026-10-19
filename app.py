"""Streamlit UI for testing the financial document summarizer agent locally.

Run with: streamlit run app.py
"""

import uuid

import streamlit as st
from langgraph.types import Command

from agent import SAMPLE_DOCUMENT, build_agent

st.set_page_config(page_title="Financial Document Summarizer", page_icon="\U0001f4b0")
st.title("Financial Document Summarizer")
st.caption("SummarizationMiddleware + HumanInTheLoopMiddleware with payment escalation.")

if "agent" not in st.session_state:
    st.session_state.agent = build_agent()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None
if "history" not in st.session_state:
    st.session_state.history = []

config = {"configurable": {"thread_id": st.session_state.thread_id}}


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if block.get("type") == "text")


def _process_result(result) -> None:
    if "__interrupt__" in result:
        st.session_state.pending_interrupt = result["__interrupt__"][0]
    else:
        st.session_state.pending_interrupt = None
        st.session_state.history.append(("assistant", _text_of(result["messages"][-1].content)))


for role, text in st.session_state.history:
    with st.chat_message(role):
        st.write(text)

if st.session_state.pending_interrupt is not None:
    requests = st.session_state.pending_interrupt.value["action_requests"]
    with st.chat_message("assistant"):
        st.warning("Human approval required before this payment is processed:")
        for req in requests:
            st.write(f"**{req['name']}**")
            st.json(req["args"])
        approve_col, reject_col = st.columns(2)
        if approve_col.button("Approve", type="primary", use_container_width=True):
            decisions = [{"type": "approve"} for _ in requests]
            result = st.session_state.agent.invoke(Command(resume={"decisions": decisions}), config)
            _process_result(result)
            st.rerun()
        if reject_col.button("Reject", use_container_width=True):
            decisions = [{"type": "reject", "message": "Rejected by human reviewer."} for _ in requests]
            result = st.session_state.agent.invoke(Command(resume={"decisions": decisions}), config)
            _process_result(result)
            st.rerun()
else:
    document = st.chat_input("Paste a financial document to summarize...")
    if document:
        st.session_state.history.append(("user", document))
        result = st.session_state.agent.invoke(
            {"messages": [{"role": "user", "content": document}]}, config
        )
        _process_result(result)
        st.rerun()

with st.sidebar:
    st.subheader("Sample document")
    st.code(SAMPLE_DOCUMENT, language=None)
    if st.button("Use sample"):
        st.session_state.history.append(("user", SAMPLE_DOCUMENT))
        result = st.session_state.agent.invoke(
            {"messages": [{"role": "user", "content": SAMPLE_DOCUMENT}]}, config
        )
        _process_result(result)
        st.rerun()
    st.divider()
    if st.button("Reset conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.pending_interrupt = None
        st.session_state.history = []
        st.rerun()
