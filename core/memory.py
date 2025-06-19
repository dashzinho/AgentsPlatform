# core/memory.py
import streamlit as st

def get_memory_for_agent(agent_name):
    if "memory" not in st.session_state:
        st.session_state["memory"] = {}
    if agent_name not in st.session_state["memory"]:
        st.session_state["memory"][agent_name] = []
    return st.session_state["memory"][agent_name]

def add_message_to_memory(agent_name, role, content):
    memory = get_memory_for_agent(agent_name)
    memory.append({"role": role, "content": content})

def reset_agent_memory(agent_name=None):
    if "memory" in st.session_state:
        if agent_name:
            st.session_state["memory"].pop(agent_name, None)
        else:
            st.session_state["memory"] = {}
