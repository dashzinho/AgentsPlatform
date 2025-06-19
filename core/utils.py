import pandas as pd
import re
import json
import os
from fpdf import FPDF

EXPORT_DIR = "outputs"
os.makedirs(EXPORT_DIR, exist_ok=True)

def clean_text(text):
    import re
    return re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)

def export_to_excel(steps, filename="agent_chain_output.xlsx"):
    df = pd.DataFrame([{
        "Agent": step["agent"],
        "Input": clean_text(step["input"]),
        "Output": clean_text(step["output"])
    } for step in steps])

    filepath = os.path.join(EXPORT_DIR, filename)
    df.to_excel(filepath, index=False)
    return filepath

def export_custom_excel(output_text: str, filename="custom_layout.xlsx"):
    """
    Parse either markdown table or dict-style output and export to Excel.
    """
    export_path = os.path.join("outputs", filename)

    # --- Try parsing JSON dictionary format ---
    try:
        data = json.loads(output_text)
        if isinstance(data, dict):
            df = pd.DataFrame(list(data.items()), columns=["Field", "Value"])
            df.to_excel(export_path, index=False)
            return export_path
    except Exception:
        pass  # Not valid JSON dict, try Markdown next

    # --- Try parsing markdown-style table ---
    try:
        lines = output_text.strip().splitlines()
        rows = []
        for line in lines:
            if "|" in line and not line.strip().startswith("|---"):
                parts = [p.strip() for p in line.strip().split("|") if p.strip()]
                if len(parts) == 2:
                    rows.append(parts)
        if rows:
            df = pd.DataFrame(rows, columns=["Field", "Value"])
            df.to_excel(export_path, index=False)
            return export_path
    except Exception:
        pass  # Couldn't parse

    # --- Fallback if no table detected ---
    df = pd.DataFrame([["Error", "Could not parse layout"]], columns=["Field", "Value"])
    df.to_excel(export_path, index=False)
    return export_path

def export_to_pdf(steps, filename="final_output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ✅ Use Unicode font
    font_path = "assets/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        raise FileNotFoundError("DejaVuSans.ttf not found in /assets/")

    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)

    for step in steps:
        input_clean = step["input"].encode("utf-8", errors="ignore").decode("utf-8")
        output_clean = step["output"].encode("utf-8", errors="ignore").decode("utf-8")

        pdf.multi_cell(0, 10, f"Agent: {step['agent']}\n\nInput:\n{input_clean}\n\nOutput:\n{output_clean}\n\n---\n")

    filepath = os.path.join(EXPORT_DIR, filename)
    pdf.output(filepath)
    return filepath
