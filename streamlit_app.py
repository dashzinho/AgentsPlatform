# streamlit_app.py
import streamlit as st
from core.agent_manager import save_agent_config, list_agents_by_category, get_agent_config, load_all_agent_configs
from core.agent_chain import run_agent_chain
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from core.file_processor import process_file
from agents.base_agent import BaseAgent
from core.export_agent import ExportAgent
from core.output_generator import generate_output_file

st.set_page_config(page_title="🧠 Agentic AI Platform", layout="wide")
st.title("🧠 Agents Platform")

# --- Session state ---
if "agent_configs" not in st.session_state:
    st.session_state.agent_configs = load_all_agent_configs()

if "final_output" not in st.session_state:
    st.session_state.final_output = None

if "steps" not in st.session_state:
    st.session_state.steps = []

if "generated_file_path" not in st.session_state:
    st.session_state.generated_file_path = None

# --- Agent Creation UI ---
with st.expander("➕ Create a New Agent"):
    with st.form("agent_creator"):
        name = st.text_input("Agent Name")
        prompt = st.text_area("Agent Prompt (System Role)")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        model = st.selectbox("Model", ["mistral", "llama3", "gemma"])
        category = st.text_input("Agent Category (e.g. researcher, summarizer, critic)")
        response_format = st.text_area("Optional: JSON Response Format", placeholder='e.g. { "summary": "...", "score": 0.0 }')
        submitted = st.form_submit_button("💾 Save Agent")

        if submitted:
            if not name or not prompt:
                st.error("Name and prompt are required.")
            else:
                st.session_state.agent_configs.append({
                    "name": name,
                    "prompt": prompt,
                    "temperature": temperature,
                    "model": model,
                    "category": category if category.strip() else "Uncategorized",
                    "response_format": response_format if response_format.strip() else None
                })
                st.success(f"✅ Agent '{name}' saved successfully!")
                st.rerun()

# --- Agent Selection ---
st.subheader("🔗 Build a Multi-Agent Chain")
agents_by_category = list_agents_by_category()

selected_agent_names = []
for category, agents in agents_by_category.items():
    with st.expander(f"📂 {category}"):
        selections = st.multiselect(
            f"Select agents in order for '{category}'",
            agents,
            key=category
        )
        selected_agent_names.extend(selections)

selected_agents = []
for agent_name in selected_agent_names:
    matching = [a for a in st.session_state.agent_configs if a["name"] == agent_name]
    if matching:
        conf = matching[0]
        selected_agents.append(BaseAgent(
            name=conf["name"],
            prompt=conf["prompt"],
            model=conf.get("model", "mistral")
        ))
    else:
        st.warning(f"⚠️ Agent config not found for: {agent_name}")

# --- File Upload ---
st.subheader("📎 Upload Files (Multiple supported)")
uploaded_files = st.file_uploader(
    "Upload PDFs, TXTs, CSVs, Excel files, or Images",
    type=["pdf", "txt", "csv", "xlsx", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

file_contents = []
if uploaded_files:
    for file in uploaded_files:
        try:
            file_type, content = process_file(file)
            file_contents.append((file.name, file_type, content))
        except Exception as e:
            st.error(f"Failed to process {file.name}: {e}")

    if file_contents:
        st.success(f"✅ {len(file_contents)} file(s) loaded.")

# --- Modes ---
mode = st.radio("How should the files be processed?", ["Unified Mode", "Batch Mode"])
pass_context = st.toggle("🔄 Pass output from one agent to the next?", value=True)

# --- Prompts ---
user_prompt = st.text_area("💬 Your task/prompt (e.g., analyze, summarize, extract...)")
user_export_instruction = st.text_input("📤 How should the output file be generated?",
    placeholder="e.g. Generate a summary in Word or create an Excel table with key fields.")

# --- Run Agent Chain ---
if st.button("🚀 Run Agent Chain", use_container_width=True):
    if not selected_agents:
        st.warning("Please select agents.")
    elif not uploaded_files and not user_prompt.strip():
        st.warning("Provide at least a prompt or one file.")
    else:
        if mode == "Unified Mode":
            merged_input = ""
            for name, _, content in file_contents:
                merged_input += f"[{name}]\n{content}\n\n"
            merged_input += user_prompt
            st.session_state.steps, st.session_state.final_output = run_agent_chain(
                merged_input, selected_agents, pass_context=pass_context
            )
        else:
            all_steps = []
            combined_output = ""
            for name, _, content in file_contents:
                full_input = f"[{name}]\n{content}\n\n{user_prompt}"
                steps, output = run_agent_chain(full_input, selected_agents, pass_context=pass_context)
                combined_output += f"📄 **{name}**\n\n{output}\n\n---\n\n"
                all_steps.extend(steps)
            st.session_state.steps = all_steps
            st.session_state.final_output = combined_output

        # --- Export file from agent ---
        if user_export_instruction.strip():
            with st.spinner("🛠 Generating output file based on your instructions..."):
                exporter = ExportAgent()
                export_instruction = exporter.run(st.session_state.final_output, user_export_instruction)
                st.session_state.generated_file_path = generate_output_file(export_instruction)

# --- Persistent Display ---
if st.session_state.final_output:
    st.success("✅ Agent Chain Completed")
    st.subheader("🪜 Steps")
    for step in st.session_state.steps:
        with st.expander(f"🧠 {step['agent']}", expanded=False):
            st.markdown(f"**Input:**\n```\n{step['input']}\n```")
            st.markdown(f"**Output:**\n```\n{step['output']}\n```")

    st.subheader("🧾 Final Output")
    st.code(st.session_state.final_output)

    if st.session_state.generated_file_path:
        with open(st.session_state.generated_file_path, "rb") as f:
            st.download_button(
                "⬇️ Download Generated Output File",
                f,
                file_name=st.session_state.generated_file_path.split("/")[-1]
            )
