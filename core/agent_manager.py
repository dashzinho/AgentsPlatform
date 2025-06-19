import os
import json
from agents.base_agent import BaseAgent
import streamlit as st

AGENT_CONFIG_DIR = "configs"

def save_agent_config(agent_dict):
    os.makedirs(AGENT_CONFIG_DIR, exist_ok=True)
    filename = f"{agent_dict['name'].replace(' ', '_')}.json"
    path = os.path.join(AGENT_CONFIG_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(agent_dict, f, indent=2)

def list_saved_agents():
    os.makedirs(AGENT_CONFIG_DIR, exist_ok=True)
    return [f[:-5] for f in os.listdir(AGENT_CONFIG_DIR) if f.endswith(".json")]

def load_agent(name):
    filepath = os.path.join(AGENT_CONFIG_DIR, f"{name}.json")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BaseAgent(
        name=data["name"],
        prompt=data["prompt"],
        model=data.get("model", "mistral"),
        temperature=data.get("temperature", 0.7),
        response_format=data.get("response_format")
    )

def get_agent_config(name):
    filepath = os.path.join(AGENT_CONFIG_DIR, f"{name}.json")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_all_agent_configs():
    if not os.path.exists(AGENT_CONFIG_DIR):
        return []

    configs = []
    for fname in os.listdir(AGENT_CONFIG_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(AGENT_CONFIG_DIR, fname), "r", encoding="utf-8") as f:
                try:
                    configs.append(json.load(f))
                except Exception as e:
                    print(f"Failed to load {fname}: {e}")
    return configs

def list_agents_by_category():
    agents = st.session_state.get("agent_configs", [])
    agents_by_category = {}
    for agent in agents:
        cat = agent.get("category", "Uncategorized") or "Uncategorized"
        agents_by_category.setdefault(cat, []).append(agent["name"])
    return agents_by_category