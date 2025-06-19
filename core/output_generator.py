import os
import json
import pandas as pd
from fpdf import FPDF
from docx import Document

EXPORT_DIR = "outputs"
os.makedirs(EXPORT_DIR, exist_ok=True)

def generate_output_file(agent_response: str) -> str:
    try:
        # --- Clean up wrapped model responses (e.g., ```json blocks)
        cleaned = agent_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        parsed = json.loads(cleaned.strip())

    except Exception as e:
        return save_txt("export_error.txt", f"❌ Failed to parse ExportAgent output:\n{e}\n\nRaw:\n{agent_response}")

    # --- Normalize file type
    file_type_raw = parsed.get("file_type", "").lower().strip()
    aliases = {
        "xlsx": "excel",
        "xls": "excel",
        "csv": "csv",
        "word": "docx",
        "doc": "docx",
        "text": "txt",
        "plain": "txt",
        "markdown": "txt"
    }
    file_type = aliases.get(file_type_raw, file_type_raw)

    filename = parsed.get("filename", f"output.{file_type}")
    content = parsed.get("content", {})

    # --- Dispatch to the correct writer
    if file_type == "txt":
        return save_txt(filename, content)
    elif file_type == "excel":
        return save_excel(filename, content)
    elif file_type == "docx":
        return save_docx(filename, content)
    elif file_type == "pdf":
        return save_pdf(filename, content)
    elif file_type == "csv":
        return save_csv(filename, content)

    return save_txt("fallback.txt", f"❌ Unsupported file type: {file_type_raw} → normalized to: {file_type}")

# ---- Format-specific handlers ----

def save_txt(filename, content: str):
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def save_excel(filename, content: dict):
    path = os.path.join(EXPORT_DIR, filename)
    rows = content.get("rows", [])
    columns = content.get("columns", [])

    if not rows or not columns:
        # fallback message
        df = pd.DataFrame([["ERROR", "Missing 'rows' or 'columns' in export_agent output"]], columns=["Field", "Value"])
    else:
        df = pd.DataFrame(rows, columns=columns)

    df.to_excel(path, index=False)
    return path

def save_csv(filename, content: dict):
    path = os.path.join(EXPORT_DIR, filename)
    df = pd.DataFrame(content["rows"], columns=content["columns"])
    df.to_csv(path, index=False)
    return path

def save_docx(filename, content):
    path = os.path.join(EXPORT_DIR, filename)
    doc = Document()

    # If content is just a string, write it as a paragraph
    if isinstance(content, str):
        doc.add_paragraph(content)
        doc.save(path)
        return path

    # Otherwise, use the structured format
    if title := content.get("title"):
        doc.add_heading(title, level=0)

    for section in content.get("sections", []):
        doc.add_heading(section.get("heading", ""), level=1)
        doc.add_paragraph(section.get("body", ""))

    doc.save(path)
    return path


def save_pdf(filename, content: dict):
    path = os.path.join(EXPORT_DIR, filename)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    if "title" in content:
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, content["title"], ln=True)
        pdf.set_font("Arial", size=12)

    for section in content.get("sections", []):
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, section.get("heading", ""), ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, section.get("body", ""))
        pdf.ln()

    pdf.output(path)
    return path
