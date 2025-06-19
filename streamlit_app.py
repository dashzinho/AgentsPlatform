# streamlit_app.py
import streamlit as st
from core.agent_manager import save_agent_config, list_agents_by_category, get_agent_config, load_all_agent_configs
from core.agent_chain import run_agent_chain
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from core.file_processor import process_file
from agents.base_agent import BaseAgent
from core.export_agent import ExportAgent
from core.output_generator import generate_output_file
from core.validator_agent import ValidatorAgent
import os
import zipfile
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

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

# --- Sidebar: File Upload + Options ---
with st.sidebar:
    st.header("📎 Upload & Settings")
    uploaded_files = st.file_uploader("Upload PDFs, TXTs, CSVs, Excel files, or Images",
        type=["pdf", "txt", "csv", "xlsx", "jpg", "jpeg", "png"], accept_multiple_files=True)

    file_contents = []
    if uploaded_files:
        for file in uploaded_files:
            try:
                file_type, content = process_file(file)
                file_contents.append((file.name, file_type, content))
            except Exception as e:
                st.error(f"❌ {file.name}: {e}")
        if file_contents:
            st.success(f"✅ {len(file_contents)} file(s) loaded.")

    mode = st.radio("How should the files be processed?", ["Unified Mode", "Batch Mode"])
    if mode == "Batch Mode":
        batch_export_style = st.radio("Export style for batch:", [
            "📁 One file per document (ZIP)", "📜 One file with multiple sheets/sections"])
    else:
        batch_export_style = None

    pass_context = st.toggle("🔄 Pass output from one agent to the next?", value=True)
    user_export_instruction = st.text_input("📄 Export instruction", placeholder="e.g. Generate Excel with summary")

# --- Agent Creation UI ---
with st.expander("➕ Create a New Agent"):
    with st.form("agent_creator"):
        name = st.text_input("Agent Name")
        prompt = st.text_area("Agent Prompt (System Role)")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        model = st.selectbox("Model", ["mistral", "llama3", "gemma"])
        category = st.text_input("Agent Category (e.g. researcher, summarizer, critic)")
        response_format = st.text_area("Optional: JSON Response Format", placeholder='e.g. { "summary": "...", "score": 0.0 }')
        submitted = st.form_submit_button("📂 Save Agent")

        if submitted and name and prompt:
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
        selections = st.multiselect(f"Select agents in order for '{category}'", agents, key=category)
        selected_agent_names.extend(selections)

selected_agents = []
for agent_name in selected_agent_names:
    match = [a for a in st.session_state.agent_configs if a["name"] == agent_name]
    if match:
        conf = match[0]
        selected_agents.append(BaseAgent(name=conf["name"], prompt=conf["prompt"], model=conf.get("model", "mistral")))
    else:
        st.warning(f"⚠️ Agent config not found for: {agent_name}")

# --- Main Prompt & Run ---
user_prompt = st.text_area("🗬️ Task prompt")

if st.button("🚀 Run Agent Chain", use_container_width=True):
    exporter = ExportAgent()
    if mode == "Unified Mode":
        merged_input = "".join(f"[{n}]\n{c}\n\n" for n, _, c in file_contents) + user_prompt
        st.session_state.steps, st.session_state.final_output = run_agent_chain(
            merged_input, selected_agents, pass_context=pass_context)

        export_instruction = exporter.run(st.session_state.final_output, user_export_instruction)
        st.session_state.generated_file_path = generate_output_file(export_instruction)

    else:
        batch_outputs, all_steps = [], []
        for name, _, content in file_contents:
            input_text = f"[{name}]\n{content}\n\n{user_prompt}"
            steps, output = run_agent_chain(input_text, selected_agents, pass_context=pass_context)
            batch_outputs.append((name, output))
            all_steps.extend(steps)
        st.session_state.steps = all_steps
        st.session_state.final_output = "\n\n".join(o for _, o in batch_outputs)

        if batch_export_style.startswith("📁"):
            zip_path = "outputs/batch_outputs.zip"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for name, output in batch_outputs:
                    inst = exporter.run(output, user_export_instruction)
                    out_path = generate_output_file(inst)
                    zipf.write(out_path, arcname=os.path.basename(out_path))
            st.session_state.generated_file_path = zip_path

        elif batch_export_style.startswith("📜"):
            wb = Workbook()
            wb.remove(wb.active)
            for name, output in batch_outputs:
                inst = exporter.run(output, user_export_instruction)
                try:
                    parsed = json.loads(inst)
                    content = parsed.get("content", {})

                    if isinstance(content, list) and all(isinstance(row, list) for row in content):
                        df = pd.DataFrame(content[1:], columns=content[0])
                    else:
                        rows = content.get("rows", [])
                        cols = content.get("columns", [])
                        df = pd.DataFrame(rows, columns=cols)

                    ws = wb.create_sheet(title=os.path.splitext(name)[0][:31])
                    for r in dataframe_to_rows(df, index=False, header=True):
                        ws.append(r)
                except Exception as e:
                    st.error(f"Failed sheet for {name}: {e}")
            multi_path = "outputs/batch_multi.xlsx"
            wb.save(multi_path)
            st.session_state.generated_file_path = multi_path

    fallback_path = "outputs/fallback.txt"
    gen = st.session_state.generated_file_path
    if not gen or not os.path.exists(gen) or gen.endswith("fallback.txt"):
        if os.path.exists(fallback_path):
            with open(fallback_path, "r") as f:
                error_msg = f.read()
            validator = ValidatorAgent()
            new_prompt = validator.generate_new_prompt(user_export_instruction, error_msg)
            st.info(f"🔁 Retrying with:\n{new_prompt}")
            export_instruction = exporter.run(st.session_state.final_output, new_prompt)
            st.session_state.generated_file_path = generate_output_file(export_instruction)

# --- Display Results ---
if st.session_state.final_output:
    st.success("✅ Chain Complete")
    st.subheader("🩜 Steps")
    for step in st.session_state.steps:
        with st.expander(f"🧠 {step['agent']}"):
            st.markdown(f"**Input:**\n```{step['input']}\n```")
            st.markdown(f"**Output:**\n```{step['output']}\n```")

    st.subheader("🗾️ Final Output")
    st.code(st.session_state.final_output)

    if st.session_state.generated_file_path:
        with open(st.session_state.generated_file_path, "rb") as f:
            st.download_button("⬇️ Download Output", f, file_name=os.path.basename(st.session_state.generated_file_path))
